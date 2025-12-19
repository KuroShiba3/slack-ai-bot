from typing import Literal, Type
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command, Send, END

from ....domain.model import Task
from ...llm import ModelFactory
from ...slack import SlackMessageService
from ....log import get_logger
from ...service import BaseState, MessageService, TaskStateService
from .prompts import get_plan_tasks_system, get_final_answer_system, get_final_answer_human


logger = get_logger(__name__)

class SupervisorAgent:
    def __init__(self,
                state: BaseState,
                model_factory: ModelFactory,
                slack_service: SlackMessageService,
                message_service: Type[MessageService] = MessageService,
                task_service: Type[TaskStateService] = TaskStateService):
        self._state = state
        self._model_factory = model_factory
        self._slack_service = slack_service
        self._MessageService = message_service
        self._TaskService = task_service

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
            await self._slack_service.add_reaction(self._channel_id, self._message_ts, "eyes")

            model = self._model_factory.create(model_name)

            # messagesを正規化
            normalized_messages = self._MessageService.normalize_messages(messages)
            messages = [system_message] + normalized_messages

            plan = await model.with_structured_output(TaskPlan).ainvoke(messages)

            if not plan.tasks:
                raise ValueError("生成されたタスクが空です")

            tasks_for_state = []
            sends = []
            for task_info in plan.tasks:
                if task_info.next_agent == "web_search":
                    task = Task.create_web_search(task_info.task_description)
                elif task_info.next_agent == "general_answer":
                    task = Task.create_general_answer(task_info.task_description)
                else:
                    raise ValueError(f"不明なエージェントです: {task_info.next_agent}")

                task_state = task.to_dict()
                tasks_for_state.append(task_state)

                sends.append(
                    Send(
                        task_state["agent_name"],
                        {
                            "task_id": task_state["id"],
                            "task_description": task_state["description"],
                            "context": self._context
                        }
                    )
                )

            return Command(
                update={"tasks": tasks_for_state},
                goto=sends
            )
        except Exception as e:
            logger.error(f"plan_tasksでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def generate_final_answer(self, model_name: str) -> Command:

        try:
            # タスク結果を取得
            task_results_text = self._TaskService.get_task_results_text(self._state)

            if not task_results_text:
                error_msg = "タスクが存在しません"
                logger.error(f"generate_final_answer: {error_msg}")
                raise ValueError(error_msg)

            # messagesから最新のユーザーメッセージを取得
            messages = self._state.get("messages", [])
            latest_question = self._MessageService.get_last_user_message(messages)

            system_message = SystemMessage(content=get_final_answer_system())

            human_message = HumanMessage(
                content=get_final_answer_human(
                    latest_question,
                    task_results_text
                )
            )

            model = self._model_factory.create(model_name)

            # messagesを正規化
            normalized_messages = self._MessageService.normalize_messages(messages)

            response = await model.ainvoke([system_message] + normalized_messages[:-1] + [human_message])

            return Command(
                update={
                    "messages": [response],
                    "final_answer": response.content
                },
                goto=END
            )
        except Exception as e:
            logger.error(f"generate_final_answerでエラーが発生しました: {str(e)}", exc_info=True)
            raise