from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command

from ...llm import ModelFactory
from .....log import get_logger
from .....domain.model import Task, TaskStatus
from ...graph.workflow_service import BaseState
from ...utils.message_converter import MessageConverter
from .prompts import get_general_answer_system

logger = get_logger(__name__)


class GeneralAnswerAgent:
    def __init__(self, state: BaseState, model_factory: ModelFactory):
        self._state = state
        self._model_factory = model_factory

        self._conversation = state.get("conversation")
        self._context = state.get("context")
        self._task_plan = state.get("task_plan")

        # Sendから渡されるパラメータ
        self._task_id = state.get("task_id")
        self._task_description = state.get("task_description")

    async def execute_task(self, model_name: str) -> Command:
        """タスクを実行して結果を返す"""

        if not self._task_description:
            logger.warning("Task description is missing")
            raise ValueError("タスクの説明が見つかりません")

        try:
            # 会話履歴からLangChainメッセージに変換
            langchain_messages = MessageConverter.to_langchain_messages(self._conversation.messages)

            # タスク用のプロンプトを構築
            system_message = SystemMessage(content=get_general_answer_system())
            task_message = HumanMessage(content=f"次のタスクについて回答してください: {self._task_description}")

            messages = [system_message] + langchain_messages + [task_message]

            # LLMで回答生成
            model = self._model_factory.create(model_name)
            response = await model.ainvoke(messages)

            # タスクを完了状態に更新
            if self._task_plan and self._task_id:
                for task in self._task_plan.tasks:
                    if task.id == self._task_id:
                        task.complete(response.content)
                        logger.info(f"Task {self._task_id} completed")
                        break

            # SupervisorAgentに制御を戻す
            return Command(
                update={"task_plan": self._task_plan},
                goto="supervisor"
            )

        except Exception as e:
            logger.error(f"Error in execute_task: {str(e)}", exc_info=True)

            # タスクを失敗状態に更新
            if self._task_plan and self._task_id:
                for task in self._task_plan.tasks:
                    if task.id == self._task_id:
                        task.fail(str(e))
                        break

            raise