from typing import Dict, Optional

from ...domain.model.chat_session import ChatSession
from ...domain.repository.chat_session_repository import IChatSessionRepository


class InMemoryChatSessionRepository(IChatSessionRepository):
    """インメモリのチャットセッションリポジトリ（ダミー実装）"""

    def __init__(self):
        self._chat_sessions: Dict[str, ChatSession] = {}

    async def save(self, chat_session: ChatSession) -> None:
        """チャットセッションを保存（何もしない）"""
        # 現在は保存不要なのでパス
        pass

    async def find_by_thread_id(self, thread_id: str) -> Optional[ChatSession]:
        """スレッドIDでチャットセッションを取得（常にNoneを返す）"""
        # 毎回新しいセッションとして扱う
        return None

    async def find_by_id(self, chat_session_id: str) -> Optional[ChatSession]:
        """IDでチャットセッションを取得（常にNoneを返す）"""
        return None
