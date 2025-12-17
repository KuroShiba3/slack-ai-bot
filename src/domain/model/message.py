from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class Role(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"

class Message:
    def __init__(self, id: UUID, role: Role, content: str, created_at: datetime):
        if not content:
            raise ValueError("メッセージの内容が空です。")
        if not role:
            raise ValueError("ロールが空です。")

        self._id = id
        self._role = role
        self._content = content
        self._created_at = created_at

    @classmethod
    def create(cls, role: Role, content: str) -> "Message":
        return cls(id=uuid4(), role=role, content=content, created_at=datetime.now())

    @classmethod
    def reconstruct(cls, id: UUID, role: Role, content: str, created_at: datetime) -> "Message":
        return cls(id=id, role=role, content=content, created_at=created_at)

    @classmethod
    def create_user_message(cls, content: str) -> "Message":
        """ユーザーメッセージを生成"""
        return cls.create(Role.USER, content)

    @classmethod
    def create_assistant_message(cls, content: str) -> "Message":
        """アシスタントメッセージを生成"""
        return cls.create(Role.ASSISTANT, content)

    @classmethod
    def create_system_message(cls, content: str) -> "Message":
        """システムメッセージを生成"""
        return cls.create(Role.SYSTEM, content)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def role(self) -> Role:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    @property
    def created_at(self) -> str:
        return self._created_at