from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Command

from src.infrastructure.exception.agent_exception import MissingStateError

from ....domain.model import Task
from ....domain.service import (
    SearchQueryGenerationService,
    TaskResultEvaluationService,
    TaskResultGenerationService,
)
from ....log import get_logger
from ...external.web_search import SearchClient
from ..graph.state import BaseState

logger = get_logger(__name__)


class WebSearchPrivateState(TypedDict):
    task: Task
    queries: list[str] | None
    attempt: int
    feedback: str | None


class WebSearchState(BaseState, WebSearchPrivateState):
    pass


class WebSearchAgent:
    MAX_ATTEMPTS = 2

    def __init__(
        self,
        search_query_service: SearchQueryGenerationService,
        task_result_service: TaskResultGenerationService,
        task_evaluation_service: TaskResultEvaluationService,
        search_client: SearchClient,
    ):
        self.search_query_service = search_query_service
        self.task_result_service = task_result_service
        self.task_evaluation_service = task_evaluation_service
        self.search_client = search_client

    async def generate_search_queries(self, state: WebSearchState) -> Command:
        """検索クエリを生成するノード"""
        task = state.get("task")
        if not task:
            raise MissingStateError("task")

        feedback = state.get("feedback")

        queries = await self.search_query_service.execute(task, feedback=feedback)

        return Command(update={"queries": queries}, goto="execute_search")

    async def execute_search(self, state: WebSearchState) -> Command:
        """検索を実行するノード"""
        task = state.get("task")
        if not task:
            raise MissingStateError("task")

        queries = state.get("queries")
        if not queries:
            raise MissingStateError("queries")

        for query in queries:
            search_results = await self.search_client.search(query)
            task.add_web_search_attempt(query=query, results=search_results)

        return Command(update={}, goto="generate_task_result")

    async def generate_task_result(self, state: WebSearchState) -> Command:
        """タスク結果を生成するノード"""
        task = state.get("task")
        if not task:
            raise MissingStateError("task")

        attempt = state.get("attempt", 0)
        feedback = state.get("feedback")

        previous_result = task.result if attempt > 0 else None
        await self.task_result_service.execute(
            task, feedback=feedback, previous_result=previous_result
        )

        return Command(update={}, goto="evaluate_task_result")

    async def evaluate_task_result(self, state: WebSearchState) -> Command:
        """タスク結果を評価し、改善が必要か判断するノード"""
        task = state.get("task")
        if not task:
            raise MissingStateError("task")

        attempt = state.get("attempt", 0)

        evaluation = await self.task_evaluation_service.execute(task)

        if evaluation.is_satisfactory or attempt >= self.MAX_ATTEMPTS - 1:
            return Command(update={}, goto=END)

        if evaluation.need == "search":
            return Command(
                update={"attempt": attempt + 1, "feedback": evaluation.feedback},
                goto="generate_search_queries",
            )
        if evaluation.need == "generate":
            return Command(
                update={"attempt": attempt + 1, "feedback": evaluation.feedback},
                goto="generate_task_result",
            )
        return Command(update={}, goto=END)

    def build_graph(self) -> StateGraph:
        graph = StateGraph(WebSearchState)

        graph.add_node("generate_search_queries", self.generate_search_queries)
        graph.add_node("execute_search", self.execute_search)
        graph.add_node("generate_task_result", self.generate_task_result)
        graph.add_node("evaluate_task_result", self.evaluate_task_result)

        graph.set_entry_point("generate_search_queries")

        return graph.compile()  # type: ignore
