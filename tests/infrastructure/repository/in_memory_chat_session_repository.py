from copy import deepcopy

from src.domain.model.chat_session import ChatSession
from src.domain.repository import ChatSessionRepository


class InMemoryChatSessionRepository(ChatSessionRepository):
    def __init__(self):
        self._sessions: dict[str, ChatSession] = {}

    async def save(self, chat_session: ChatSession) -> None:
        """チャットセッションを保存"""
        self._sessions[chat_session.id] = deepcopy(chat_session)

    async def find_by_id(self, chat_session_id: str) -> ChatSession | None:
        """IDでチャットセッションを取得"""
        session = self._sessions.get(chat_session_id)
        if session is None:
            return None

        return deepcopy(session)

    def clear(self) -> None:
        """全てのセッションをクリア"""
        self._sessions.clear()
