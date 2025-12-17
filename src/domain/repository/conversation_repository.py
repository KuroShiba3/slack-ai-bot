from abc import ABC, abstractmethod
from ..model.conversation import Conversation

class ConversationRepository(ABC):
    """会話履歴の永続化を管理するリポジトリのインターフェース"""

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """会話を保存"""
        pass

    @abstractmethod
    async def find_by_id(self, conversation_id: str) -> Conversation | None:
        """IDで会話を取得"""
        pass