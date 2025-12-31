from copy import deepcopy
from uuid import UUID

from src.domain.model.feedback import Feedback
from src.domain.repository import FeedbackRepository


class InMemoryFeedbackRepository(FeedbackRepository):
    def __init__(self):
        # (message_id, user_id) のタプルをキーとして保存
        self._feedbacks: dict[tuple[UUID, str], Feedback] = {}

    async def find_by_message_and_user(
        self, message_id: UUID, user_id: str
    ) -> Feedback | None:
        """メッセージIDとユーザーIDでフィードバックを取得"""
        feedback = self._feedbacks.get((message_id, user_id))
        if feedback is None:
            return None
        return deepcopy(feedback)

    async def save(self, feedback: Feedback) -> None:
        """フィードバックを保存"""
        key = (feedback.message_id, feedback.user_id)
        self._feedbacks[key] = deepcopy(feedback)

    def clear(self) -> None:
        """全てのフィードバックをクリア"""
        self._feedbacks.clear()
