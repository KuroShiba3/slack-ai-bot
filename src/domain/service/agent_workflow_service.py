from abc import ABC, abstractmethod
from typing import Any

from ..model.final_answer import FinalAnswer


class AgentWorkflowService(ABC):
    @abstractmethod
    async def execute(self, user_message: str, context: dict[str, Any]) -> FinalAnswer:
        pass
