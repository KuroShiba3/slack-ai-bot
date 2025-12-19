from typing import Type
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.types import Command, END

from ...llm import ModelFactory
from ...slack import SlackMessageService
from ....log import get_logger
from ....domain.model import GeneralAnswerTaskLog
from ...service import MessageService, TaskStateService, BaseState
from .prompts import get_general_answer_system

logger = get_logger(__name__)


class GeneralAnswerAgent:
    def __init__(self,
                state: BaseState,
                model_factory: ModelFactory,
                slack_service: SlackMessageService,
                message_service: Type[MessageService] = MessageService,
                task_service: Type[TaskStateService] = TaskStateService):

        self._state = state
        self._model_factory = model_factory
        self._slack_service = slack_service
        self._message_service = message_service
        self._TaskService = task_service

        self._context = state.get("context")
        self._task_id = state.get("task_id")
        self._task_description = state.get("task_description")

    async def generate_task_answer(self, model_name: str) -> Command:
        """個別タスクに対する回答を生成してタスクログに記録"""

        if not self._task_description:
            logger.warning("Task description is missing")
            return Command(
                goto="generate_final_answer"
            )

        user_message = self._message_service.get_last_user_message(self._state.get("messages"))

        system_message = SystemMessage(content=get_general_answer_system())
        task_message = HumanMessage(content=f"次のタスクについて回答してください: {self._task_description}")

        messages = [system_message] + [user_message] + [task_message]

        try:
            model = self._model_factory.create(model_name)
            response = await model.ainvoke(messages)

            task_update = {}
            if self._task_id:
                task_update = self._TaskService.add_general_answer_attempt(
                    self._state,
                    self._task_id,
                    self._task_description,
                    response.content
                )

            return Command(
                update=task_update,
                goto="generate_final_answer"
            )

        except Exception as e:
            logger.error(f"Error in generate_task_answer: {str(e)}", exc_info=True)
            return Command(
                goto="generate_final_answer"
            )

    async def generate_final_answer(self, model_name: str) -> Command:
        """タスク結果を統合して最終回答を生成"""

        task_results = []
        if self._task_id:
            task = self._TaskService.get_task_by_id(self._state, self._task_id)
            if task and task.log:
                if isinstance(task.log, GeneralAnswerTaskLog):
                    task_results = task.log.get_all_responses()


        # 最終回答用のプロンプトを構築
        system_message = SystemMessage(content=get_general_answer_system())

        result_text = "\n".join(task_results)
        user_message = HumanMessage(
            content=f"以下の情報を踏まえて、ユーザーの質問に対する最終的な回答を生成してください:\n\n{result_text}"
        )

        messages = [system_message, user_message]

        try:
            model = self._model_factory.create(model_name)
            response = await model.ainvoke(messages)

            # タスクを完了状態に更新
            task_update = {}
            if self._task_id:
                task_update = self._TaskService.complete_task(
                    self._state,
                    self._task_id,
                    response.content
                )

            return Command(
                update={
                    **task_update,
                    "messages": [AIMessage(content=response.content)],
                    "final_answer": response.content
                },
                goto=END
            )

        except Exception as e:
            logger.error(f"Error in generate_final_answer: {str(e)}", exc_info=True)
            error_message = "An error occurred while generating the response."
            if self._task_id:
                task_update = self._TaskService.complete_task(
                    self._state,
                    self._task_id,
                    error_message
                )
                return Command(
                    update={
                        **task_update,
                        "final_answer": error_message
                    },
                    goto=END
                )
            return Command(
                update={"final_answer": error_message},
                goto=END
            )