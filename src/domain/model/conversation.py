from datetime import datetime
from uuid import UUID, uuid4

from .message import Message, Role


class Conversation:
    def __init__(self, id: UUID, messages: list[Message], created_at: datetime):
        if not messages:
            raise ValueError("メッセージが空です。")

        self._id = id
        self._messages = messages
        self._created_at = created_at

    @classmethod
    def create(cls) -> "Conversation":
        return cls(conversation_id=uuid4(), messages=[], created_at=datetime.now())

    @classmethod
    def reconstruct(cls, id: str, messages: list[Message], created_at: datetime) -> "Conversation":
        return cls(id=id, messages=messages, created_at=created_at)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def last_user_message(self) -> Message | None:
        """直近のユーザーメッセージを取得"""
        for message in reversed(self._messages):
            if message.role == Role.USER:
                return message
        return None

    def append_user_message(self, content: str) -> Message:
        """ユーザーからのメッセージを追加"""
        message = Message.create_user_message(content)
        self._messages.append(message)

    def append_assistant_message(self, content: str) -> Message:
        """アシスタントからのメッセージを追加"""
        message = Message.create_assistant_message(content)
        self._messages.append(message)

    def append_system_message(self, content: str) -> Message:
        """システムメッセージを追加"""
        message = Message.create_system_message(content)
        self._messages.append(message)
