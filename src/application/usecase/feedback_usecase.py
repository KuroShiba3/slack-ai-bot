from uuid import UUID

from ...domain.model.feedback import Feedback, FeedbackType
from ...domain.repository import FeedbackRepository
from ...log import get_logger
from ..dto.feedback_usecase import FeedbackInput
from ..exception.usecase_exception import InvalidInputError

logger = get_logger(__name__)


class FeedbackUseCase:
    def __init__(self, feedback_repository: FeedbackRepository):
        self._feedback_repository = feedback_repository

    async def execute(self, input_dto: FeedbackInput) -> FeedbackInput:
        if not input_dto.message_id:
            raise InvalidInputError("message_id")
        if not input_dto.feedback_type:
            raise InvalidInputError("feedback_type")
        if not input_dto.user_id:
            raise InvalidInputError("user_id")

        feedback_type = FeedbackType(input_dto.feedback_type)
        message_id = UUID(input_dto.message_id)

        existing_feedback = await self._feedback_repository.find_by_message_and_user(
            message_id=message_id,
            user_id=input_dto.user_id,
        )

        if existing_feedback:
            # 既存のフィードバックを更新
            if feedback_type == FeedbackType.GOOD:
                existing_feedback.make_positive()
            else:
                existing_feedback.make_negative()

            await self._feedback_repository.save(existing_feedback)
        else:
            # 見つからない場合は新規作成
            feedback = Feedback.create(
                user_id=input_dto.user_id,
                message_id=message_id,
                feedback=feedback_type,
            )
            await self._feedback_repository.save(feedback)
