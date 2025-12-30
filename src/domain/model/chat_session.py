from datetime import datetime

from src.domain.exception.chat_session_exception import (
    AssistantMessageNotFoundError,
    InvalidAssistantMessageRoleError,
    InvalidUserMessageRoleError,
    NoneTaskPlanError,
    UserMessageNotFoundError,
)

from .message import Message, Role
from .task_plan import TaskPlan


class ChatSession:
    def __init__(
        self,
        id: str,
        thread_id: str | None,
        user_id: str,
        channel_id: str,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime,
        updated_at: datetime,
    ):
        self._id = id
        self._thread_id = thread_id
        self._user_id = user_id
        self._channel_id = channel_id
        self._messages = messages
        self._task_plans = task_plans
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(
        cls, id: str, thread_id: str | None, user_id: str, channel_id: str
    ) -> "ChatSession":
        now = datetime.now()
        return cls(
            id=id,
            thread_id=thread_id,
            user_id=user_id,
            channel_id=channel_id,
            messages=[],
            task_plans=[],
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def reconstruct(
        cls,
        id: str,
        thread_id: str | None,
        user_id: str,
        channel_id: str,
        messages: list[Message],
        task_plans: list[TaskPlan],
        created_at: datetime,
        updated_at: datetime,
    ) -> "ChatSession":
        return cls(
            id=id,
            thread_id=thread_id,
            user_id=user_id,
            channel_id=channel_id,
            messages=messages,
            task_plans=task_plans,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def thread_id(self) -> str | None:
        return self._thread_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def task_plans(self) -> list[TaskPlan]:
        return self._task_plans

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def last_user_message(self) -> Message:
        """直近のユーザーメッセージを取得"""
        for message in reversed(self._messages):
            if message.role == Role.USER:
                return message
        raise UserMessageNotFoundError()

    def last_assistant_message_id(self) -> str:
        """直近のアシスタントメッセージのIDを取得"""
        for message in reversed(self._messages):
            if message.role == Role.ASSISTANT:
                return str(message.id)
        raise AssistantMessageNotFoundError()

    def add_user_message(self, content: str | Message):
        """ユーザーからのメッセージを追加"""
        if isinstance(content, Message):
            if content.role != Role.USER:
                raise InvalidUserMessageRoleError()
            self._messages.append(content)
        else:
            message = Message.create_user_message(content)
            self._messages.append(message)

    def add_assistant_message(self, content: str | Message):
        """アシスタントからのメッセージを追加"""
        if isinstance(content, Message):
            if content.role != Role.ASSISTANT:
                raise InvalidAssistantMessageRoleError()
            self._messages.append(content)
        else:
            message = Message.create_assistant_message(content)
            self._messages.append(message)

    def add_task_plan(self, task_plan: TaskPlan):
        """タスク計画を追加"""
        if task_plan is None:
            raise NoneTaskPlanError()
        self._task_plans.append(task_plan)
