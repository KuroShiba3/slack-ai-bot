from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class FeedbackType(Enum):
    GOOD = "good"
    BAD = "bad"


class Feedback:
    def __init__(
        self,
        id: UUID,
        user_id: str,
        message_id: UUID,
        feedback: FeedbackType,
        created_at: datetime,
        updated_at: datetime,
    ):
        self._id = id
        self._user_id = user_id
        self._message_id = message_id
        self._feedback = feedback
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(cls, user_id: str, message_id: UUID, feedback: FeedbackType) -> "Feedback":
        created_at = datetime.now()
        updated_at = created_at
        return cls(
            id=uuid4(),
            user_id=user_id,
            message_id=message_id,
            feedback=feedback,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def reconstruct(
        cls,
        id: UUID,
        user_id: str,
        message_id: UUID,
        feedback: FeedbackType,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Feedback":
        return cls(
            id=id,
            user_id=user_id,
            message_id=message_id,
            feedback=feedback,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def message_id(self) -> UUID:
        return self._message_id

    @property
    def feedback(self) -> FeedbackType:
        return self._feedback

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def is_positive(self) -> bool:
        return self._feedback == FeedbackType.GOOD

    def is_negative(self) -> bool:
        return self._feedback == FeedbackType.BAD

    def make_positive(self) -> None:
        """フィードバックをポジティブに変更"""
        if self.is_positive():
            return
        self._feedback = FeedbackType.GOOD
        self._updated_at = datetime.now()

    def make_negative(self) -> None:
        """フィードバックをネガティブに変更"""
        if self.is_negative():
            return
        self._feedback = FeedbackType.BAD
        self._updated_at = datetime.now()
