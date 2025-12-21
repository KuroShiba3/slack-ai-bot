from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, Send
from langgraph.graph import StateGraph, END

from .....domain.model import Task, TaskPlan
from .....log import get_logger
from ....llm import ModelFactory
from ...graph.state import BaseState
from ...utils.message_converter import MessageConverter
from .prompts import get_plan_tasks_system, get_final_answer_system, get_final_answer_human


logger = get_logger(__name__)

class SupervisorAgent:
    def __init__(self, model_factory: ModelFactory):
        self._model_factory = model_factory

    async def plan_tasks(self, state: BaseState, config: RunnableConfig | None = None) -> Command:

        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("plan_tasks_model", configurable.get("default_model", "gemini-2.0-flash"))

        class _Task(BaseModel):
            task_description: str = Field(description="タスクの内容を簡潔に記述してください。")
            next_agent: Literal["general_answer", "web_search"] = Field(description="処理するエージェント")

        class _TaskPlan(BaseModel):
            tasks: list[_Task] = Field(description="実行するタスクのリスト（最低1つ以上）")
            reason: str = Field(description="タスク分割の戦略と根拠を説明してください。")

        chat_session = state.get("chat_session")
        if not chat_session:
            raise ValueError("chat_sessionがステートに存在しません")

        try:

            langchain_messages = MessageConverter.to_langchain_messages(chat_session.messages)
            system_message = SystemMessage(content=get_plan_tasks_system())
            messages = [system_message] + langchain_messages

            model = self._model_factory.create(model_name)

            plan = await model.with_structured_output(_TaskPlan).ainvoke(messages)

            if not plan.tasks:
                raise ValueError("生成されたタスクが空です")

            tasks = []
            sends = []
            for task_info in plan.tasks:
                if task_info.next_agent == "web_search":
                    task = Task.create_web_search(task_info.task_description)
                    tasks.append(task)
                elif task_info.next_agent == "general_answer":
                    task = Task.create_general_answer(task_info.task_description)
                    tasks.append(task)
                else:
                    raise ValueError(f"不明なエージェントです: {task_info.next_agent}")

                sends.append(
                    Send(
                        task.agent_name.value,
                        {"task_id": str(task.id)}
                    )
                )

            # TaskPlanドメインモデルを作成
            latest_message = chat_session.last_user_message()
            if not latest_message:
                raise ValueError("ユーザーメッセージが見つかりません")

            task_plan = TaskPlan.create(
                message_id=latest_message.id,
                tasks=tasks
            )

            # SendにはBaseStateの全フィールドを含める必要がある
            # これによりサブグラフでもBaseStateにアクセスできる
            updated_sends = [
                Send(
                    task.agent_name.value,
                    {
                        "task_id": str(task.id),
                        "chat_session": chat_session,
                        "context": state.get("context"),
                        "task_plan": task_plan,
                        "answer": None
                    }
                )
                for task in tasks
            ]

            return Command(
                update={"task_plan": task_plan},
                goto=updated_sends
            )
        except Exception as e:
            logger.error(f"plan_tasksでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def generate_final_answer(self, state: BaseState, config: RunnableConfig | None = None) -> Command:

        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("generate_final_answer_model", configurable.get("default_model", "gemini-2.0-flash"))

        try:
            chat_session = state.get("chat_session")
            if not chat_session:
                raise ValueError("chat_sessionがステートに存在しません")

            task_plan = state.get("task_plan")
            if not task_plan:
                raise ValueError("TaskPlanが見つかりません")

            task_results_text = task_plan.format_task_results()

            latest_message = chat_session.last_user_message()
            if not latest_message:
                raise ValueError("ユーザーメッセージが見つかりません")

            latest_question = latest_message.content

            system_message = SystemMessage(content=get_final_answer_system())

            human_message = HumanMessage(
                content=get_final_answer_human(
                    latest_question,
                    task_results_text
                )
            )

            langchain_messages = MessageConverter.to_langchain_messages(chat_session.messages)

            model = self._model_factory.create(model_name)

            response = await model.ainvoke([system_message] + langchain_messages[:-1] + [human_message])

            return Command(
                update={
                    "answer": response.content
                },
                goto=END
            )
        except Exception as e:
            logger.error(f"generate_final_answerでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    def build_graph(self, general_answer_graph, web_search_graph) -> StateGraph:
        """Supervisorのメイングラフを構築"""
        graph = StateGraph(BaseState)

        graph.add_node("plan_tasks", self.plan_tasks)
        graph.add_node("general_answer", general_answer_graph)
        graph.add_node("web_search", web_search_graph)
        graph.add_node("generate_final_answer", self.generate_final_answer)

        graph.set_entry_point("plan_tasks")

        graph.add_edge("general_answer", "generate_final_answer")
        graph.add_edge("web_search", "generate_final_answer")
        graph.add_edge("generate_final_answer", END)

        return graph.compile()