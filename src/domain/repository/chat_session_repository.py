from typing import Protocol

from ..model.chat_session import ChatSession


class ChatSessionRepository(Protocol):
    async def save(self, chat_session: ChatSession) -> None:
        """チャットセッションを保存"""
        ...

    async def find_by_id(self, chat_session_id: str) -> ChatSession | None:
        """IDでチャットセッションを取得"""
        ...
