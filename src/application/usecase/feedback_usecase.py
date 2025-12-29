from uuid import UUID

from ...domain.model.feedback import Feedback, FeedbackType
from ...domain.repository import FeedbackRepository
from ...log import get_logger
from ..dto.feedback_usecase import FeedbackInput

logger = get_logger(__name__)


class FeedbackUseCase:
    def __init__(self, feedback_repository: FeedbackRepository):
        self._feedback_repository = feedback_repository

    async def execute(self, input_dto: FeedbackInput) -> FeedbackInput:
        try:
            feedback_type = FeedbackType(input_dto.feedback_type)
            message_id = UUID(input_dto.message_id)

            # 既存のフィードバックを取得
            existing_feedback = (
                await self._feedback_repository.find_by_message_and_user(
                    message_id=message_id,
                    user_id=input_dto.user_id,
                )
            )

            if existing_feedback:
                if feedback_type == FeedbackType.GOOD:
                    existing_feedback.make_positive()
                else:
                    existing_feedback.make_negative()

                await self._feedback_repository.save(existing_feedback)
                logger.debug(
                    f"フィードバックを更新しました: message_id={message_id}, type={feedback_type.value}"
                )
            else:
                feedback = Feedback.create(
                    user_id=input_dto.user_id,
                    message_id=message_id,
                    feedback=feedback_type,
                )
                await self._feedback_repository.save(feedback)
                logger.debug(
                    f"フィードバックを作成しました: message_id={message_id}, type={feedback_type.value}"
                )

        except Exception as e:
            logger.error(f"フィードバックの保存に失敗しました: {e}", exc_info=True)
