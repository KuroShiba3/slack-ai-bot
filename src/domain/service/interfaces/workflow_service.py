from typing import Any, Protocol

from ...model import ChatSession, WorkflowResult


class IWorkflowService(Protocol):
    async def execute(
        self, chat_session: ChatSession, context: dict[str, Any]
    ) -> WorkflowResult:
        """チャットセッションを元にワークフローを実行し、結果を返す"""
        ...
