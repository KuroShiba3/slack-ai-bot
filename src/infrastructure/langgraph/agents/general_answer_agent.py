from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Command

from src.infrastructure.exception.agent_exception import MissingStateError

from ....domain.model import Task
from ....domain.service import GeneralAnswerService
from ....log import get_logger
from ..graph.state import BaseState

logger = get_logger(__name__)


class GeneralAnswerPrivateState(TypedDict):
    task: Task


class GeneralAnswerState(BaseState, GeneralAnswerPrivateState):
    pass


class GeneralAnswerAgent:
    def __init__(self, general_answer_service: GeneralAnswerService):
        self.general_answer_service = general_answer_service

    async def generate_answer(self, state: GeneralAnswerState) -> Command:
        """一般回答を生成するノード"""
        task = state.get("task")
        if not task:
            raise MissingStateError("task")

        chat_session = state.get("chat_session")
        if not chat_session:
            raise MissingStateError("chat_session")

        await self.general_answer_service.execute(chat_session, task)

        return Command(update={}, goto=END)

    def build_graph(self) -> StateGraph:
        graph = StateGraph(GeneralAnswerState)

        graph.add_node("generate_answer", self.generate_answer)

        graph.set_entry_point("generate_answer")

        return graph.compile()  # type: ignore
