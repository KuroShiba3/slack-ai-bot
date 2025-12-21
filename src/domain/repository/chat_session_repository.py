from abc import ABC, abstractmethod

from ..model.chat_session import ChatSession


class IChatSessionRepository(ABC):
    """チャットセッションの永続化を管理するリポジトリのインターフェース"""

    @abstractmethod
    async def save(self, chat_session: ChatSession) -> None:
        """チャットセッションを保存"""
        pass

    @abstractmethod
    async def find_by_id(self, chat_session_id: str) -> ChatSession | None:
        """IDでチャットセッションを取得"""
        pass