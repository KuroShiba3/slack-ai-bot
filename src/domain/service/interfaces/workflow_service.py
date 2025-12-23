from abc import ABC, abstractmethod
from typing import Any

from ...model import ChatSession, WorkflowResult


class IWorkflowService(ABC):
    @abstractmethod
    async def execute(self, chat_session: ChatSession, context: dict[str, Any]) -> WorkflowResult:
        """チャットセッションを元にワークフローを実行し、結果を返す

        Args:
            chat_session: チャットセッション（ユーザーメッセージを含む）
            context: 実行コンテキスト

        Returns:
            WorkflowResult: 回答とタスク計画を含む実行結果
        """
        pass
