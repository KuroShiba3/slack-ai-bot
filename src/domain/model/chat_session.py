from datetime import datetime

from .message import Message, Role
from .task_plan import TaskPlan


class ChatSession:
    def __init__(
        self,
        id: str,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime,
    ):
        self._id = id
        self._messages = messages
        self._task_plans = task_plans
        self._created_at = created_at

    @classmethod
    def create(cls, id: str) -> "ChatSession":
        return cls(id=id, messages=[], task_plans=[], created_at=datetime.now())

    @classmethod
    def reconstruct(
        cls,
        id: str,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime,
    ) -> "ChatSession":
        return cls(
            id=id, messages=messages, task_plans=task_plans, created_at=created_at
        )

    @property
    def id(self) -> str:
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

    def last_assistant_message_id(self) -> str | None:
        """直近のアシスタントメッセージのIDを取得"""
        for message in reversed(self._messages):
            if message.role == Role.ASSISTANT:
                return str(message.id)
        return None

    def add_user_message(self, content: str | Message):
        """ユーザーからのメッセージを追加"""
        if isinstance(content, Message):
            if content.role != Role.USER:
                raise ValueError("USER以外のメッセージは追加できません")
            self._messages.append(content)
        else:
            message = Message.create_user_message(content)
            self._messages.append(message)

    def add_assistant_message(self, content: str | Message):
        """アシスタントからのメッセージを追加"""
        if isinstance(content, Message):
            if content.role != Role.ASSISTANT:
                raise ValueError("ASSISTANT以外のメッセージは追加できません")
            self._messages.append(content)
        else:
            message = Message.create_assistant_message(content)
            self._messages.append(message)

    def add_task_plan(self, task_plan: TaskPlan):
        """タスク計画を追加"""
        self._task_plans.append(task_plan)
