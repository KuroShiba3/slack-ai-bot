from uuid import UUID

from ..dto.feedback_usecase import FeedbackInput
from ...domain.model.feedback import Feedback, FeedbackType
from ...domain.repository import FeedbackRepository
from ...log import get_logger

logger = get_logger(__name__)


class FeedbackUseCase:
    def __init__(self, feedback_repository: FeedbackRepository):
        self._feedback_repository = feedback_repository

    async def execute(self, input_dto: FeedbackInput) -> FeedbackInput:
        try:
            feedback_type = FeedbackType(input_dto.feedback_type)

            feedback = Feedback.create(
                user_id=input_dto.user_id,
                message_id=UUID(input_dto.message_id),
                feedback=feedback_type,
            )

            await self._feedback_repository.save(feedback)

            logger.debug(
                f"フィードバックを保存しました: message_id={input_dto.message_id}, type={input_dto.feedback_type}"
            )

        except Exception as e:
            logger.error(f"フィードバックの保存に失敗しました: {e}", exc_info=True)