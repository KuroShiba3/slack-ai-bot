from abc import ABC, abstractmethod
from typing import Dict, Any
from ..model.final_answer import FinalAnswer

class AgentWorkflowService(ABC):
    @abstractmethod
    async def execute(self, user_message: str, context: Dict[str, Any]) -> FinalAnswer:
        pass