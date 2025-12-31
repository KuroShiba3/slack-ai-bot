from langgraph.graph import END
from langgraph.types import Command, Send

from src.infrastructure.exception.agent_exception import MissingStateError

from ....domain.model import AgentName
from ....domain.service import FinalAnswerService, TaskPlanningService
from ....log import get_logger
from ..graph.state import BaseState

logger = get_logger(__name__)


class SupervisorAgent:
    def __init__(
        self,
        task_planning_service: TaskPlanningService,
        final_answer_service: FinalAnswerService,
    ):
        self.task_planning_service = task_planning_service
        self.final_answer_service = final_answer_service

    async def plan_tasks(self, state: BaseState) -> Command:
        """タスク計画を生成し、各タスクを並列実行するノード"""
        chat_session = state.get("chat_session")
        if not chat_session:
            raise MissingStateError("chat_session")

        task_plan = await self.task_planning_service.execute(chat_session)

        chat_session.add_task_plan(task_plan)

        sends = []
        for task in task_plan.tasks:
            send_data = {
                "task": task,
                "chat_session": chat_session,
            }

            if task.agent_name == AgentName.WEB_SEARCH:
                send_data.update(
                    {
                        "attempt": 0,
                        "feedback": None,
                        "queries": None,
                    }
                )

            sends.append(Send(task.agent_name.value, send_data))

        return Command(update={"task_plan": task_plan}, goto=sends)

    async def generate_final_answer(self, state: BaseState) -> Command:
        """最終回答を生成するノード"""
        try:
            chat_session = state.get("chat_session")
            if not chat_session:
                raise MissingStateError("chat_session")

            task_plan = state.get("task_plan")
            if not task_plan:
                raise MissingStateError("task_plan")

            answer_message = await self.final_answer_service.execute(
                chat_session, task_plan
            )

            return Command(update={"answer": answer_message.content}, goto=END)

        except Exception as e:
            logger.error(f"最終回答生成でエラーが発生しました: {e!s}", exc_info=True)
            raise
