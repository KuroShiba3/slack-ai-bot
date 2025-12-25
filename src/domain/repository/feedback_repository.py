from typing import Protocol

from ..model.feedback import Feedback


class FeedbackRepository(Protocol):
    async def save(self, feedback: Feedback) -> None:
        """フィードバックを保存"""
        ...