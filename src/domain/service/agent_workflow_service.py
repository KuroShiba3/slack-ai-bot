from abc import ABC, abstractmethod
from typing import Any

from ..model import Conversation, WorkflowResult


class AgentWorkflowService(ABC):
    @abstractmethod
    async def execute(self, conversation: Conversation, context: dict[str, Any]) -> WorkflowResult:
        """会話履歴を元にワークフローを実行し、結果を返す

        Args:
            conversation: 会話履歴（ユーザーメッセージを含む）
            context: 実行コンテキスト

        Returns:
            WorkflowResult: 回答とタスク計画を含む実行結果
        """
        pass
