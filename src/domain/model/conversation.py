from datetime import datetime
from uuid import UUID, uuid4

from .message import Message, Role
from .task_plan import TaskPlan


class Conversation:
    def __init__(
        self,
        id: UUID,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime
    ):
        self._id = id
        self._messages = messages
        self._task_plans = task_plans
        self._created_at = created_at

    @classmethod
    def create(cls) -> "Conversation":
        return cls(
            id=uuid4(),
            messages=[],
            task_plans=[],
            created_at=datetime.now()
        )

    @classmethod
    def reconstruct(
        cls,
        id: UUID,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime
    ) -> "Conversation":
        return cls(
            id=id,
            messages=messages,
            task_plans=task_plans,
            created_at=created_at
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def task_plans(self) -> list[TaskPlan]:
        return self._task_plans

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def last_user_message(self) -> Message | None:
        """直近のユーザーメッセージを取得"""
        for message in reversed(self._messages):
            if message.role == Role.USER:
                return message
        return None

    def add_user_message(self, content: str) -> Message:
        """ユーザーからのメッセージを追加"""
        message = Message.create_user_message(content)
        self._messages.append(message)
        return message

    def add_assistant_message(self, content: str) -> Message:
        """アシスタントからのメッセージを追加"""
        message = Message.create_assistant_message(content)
        self._messages.append(message)
        return message

    def add_task_plan(self, task_plan: TaskPlan) -> None:
        """タスク計画を追加"""
        self._task_plans.append(task_plan)

    def get_latest_task_plan(self) -> TaskPlan | None:
        """最新のタスク計画を取得"""
        return self._task_plans[-1] if self._task_plans else None
