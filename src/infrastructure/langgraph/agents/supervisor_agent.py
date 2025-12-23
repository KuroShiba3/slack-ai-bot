from langgraph.graph import END
from langgraph.types import Command, Send

from ....domain.model import AgentName
from ....domain.service import TaskPlanningService, AnswerGenerationService
from ....log import get_logger
from ..graph.state import BaseState

logger = get_logger(__name__)


class SupervisorAgent:
    """Supervisorエージェント: タスク計画と最終回答生成を担当"""

    def __init__(
        self,
        task_planning_service: TaskPlanningService,
        answer_generation_service: AnswerGenerationService
    ):
        self.task_planning_service = task_planning_service
        self.answer_generation_service = answer_generation_service

    async def plan_tasks(self, state: BaseState) -> Command:
        """タスク計画を生成し、各タスクを並列実行するノード"""
        try:
            chat_session = state.get("chat_session")
            if not chat_session:
                raise ValueError("chat_sessionがステートに存在しません")

            # タスク計画を生成
            task_plan = await self.task_planning_service.execute(chat_session)

            # ChatSessionにタスク計画を追加
            chat_session.add_task_plan(task_plan)

            logger.info(f"タスク計画生成完了: tasks_count={len(task_plan.tasks)}")

            # 各タスクを並列実行するためのSendを作成
            sends = []
            for task in task_plan.tasks:
                send_data = {
                    "task": task,
                    "chat_session": chat_session,
                }

                if task.agent_name == AgentName.WEB_SEARCH:
                    send_data.update({
                        "attempt": 0,
                        "feedback": None,
                        "queries": None,
                    })

                sends.append(Send(task.agent_name.value, send_data))

            return Command(
                update={"task_plan": task_plan},
                goto=sends
            )

        except Exception as e:
            logger.error(f"タスク計画生成でエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def generate_final_answer(self, state: BaseState) -> Command:
        """最終回答を生成するノード"""
        try:
            chat_session = state.get("chat_session")
            if not chat_session:
                raise ValueError("chat_sessionがステートに存在しません")

            task_plan = state.get("task_plan")
            if not task_plan:
                raise ValueError("TaskPlanが見つかりません")

            # 最終回答を生成
            answer_message = await self.answer_generation_service.execute(chat_session, task_plan)

            # ChatSessionに回答を追加（Messageオブジェクトを直接渡す）
            chat_session.add_assistant_message(answer_message)

            logger.info("最終回答生成完了")

            return Command(update={"answer": answer_message.content}, goto=END)

        except Exception as e:
            logger.error(f"最終回答生成でエラーが発生しました: {str(e)}", exc_info=True)
            raise
