from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command, Send, END

from .....domain.model import Task, TaskPlan
from .....log import get_logger
from ...llm import ModelFactory
from ...graph.workflow_service import BaseState
from ...utils.message_converter import MessageConverter
from .prompts import get_plan_tasks_system, get_final_answer_system, get_final_answer_human


logger = get_logger(__name__)

class SupervisorAgent:
    def __init__(self,
                state: BaseState,
                model_factory: ModelFactory):
        self._state = state
        self._model_factory = model_factory

        self._conversation = state.get("conversation")
        self._context = state.get("context")
        self._channel_id = self._context.get("channel_id")
        self._message_ts = self._context.get("message_ts")


    async def plan_tasks(self, model_name: str) -> Command:

        class _Task(BaseModel):
            task_description: str = Field(description="タスクの内容を簡潔に記述してください。")
            next_agent: Literal["general_answer", "web_search"] = Field(description="処理するエージェント")

        class TaskPlan(BaseModel):
            tasks: list[_Task] = Field(description="実行するタスクのリスト（最低1つ以上）")
            reason: str = Field(description="タスク分割の戦略と根拠を説明してください。")

        system_message = SystemMessage(content=get_plan_tasks_system())

        try:

            model = self._model_factory.create(model_name)

            langchain_messages = MessageConverter.to_langchain_messages(self._conversation.messages)
            messages = [system_message] + langchain_messages

            plan = await model.with_structured_output(TaskPlan).ainvoke(messages)

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
                        {
                            "task_id": task.id,
                            "task_description": task.description,
                            "context": self._context
                        }
                    )
                )

            # TaskPlanドメインモデルを作成
            latest_message = self._conversation.last_user_message()
            if not latest_message:
                raise ValueError("ユーザーメッセージが見つかりません")

            task_plan = TaskPlan.create(
                message_id=latest_message.id,
                tasks=tasks
            )

            return Command(
                update={"task_plan": task_plan},
                goto=sends
            )
        except Exception as e:
            logger.error(f"plan_tasksでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def generate_final_answer(self, model_name: str) -> Command:

        try:
            task_plan = self._state.get("task_plan")
            if not task_plan:
                raise ValueError("TaskPlanが見つかりません")

            task_results_text = task_plan.format_task_results()

            latest_message = self._conversation.last_user_message()
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

            model = self._model_factory.create(model_name)

            langchain_messages = MessageConverter.to_langchain_messages(self._conversation.messages)

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