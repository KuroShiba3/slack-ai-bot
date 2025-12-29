from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Command

from ....domain.model import Task
from ...external.web_search import SearchClient
from ....domain.service import (
    SearchQueryGenerationService,
    TaskResultEvaluationService,
    TaskResultGenerationService,
)
from ....log import get_logger
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
        try:
            task = state.get("task")
            if not task:
                raise ValueError("taskがステートに存在しません")

            attempt = state.get("attempt", 0)
            feedback = state.get("feedback")

            queries = await self.search_query_service.execute(task, feedback=feedback)

            return Command(update={"queries": queries}, goto="execute_search")

        except Exception as e:
            logger.error(f"検索クエリ生成でエラーが発生しました: {e!s}", exc_info=True)
            raise

    async def execute_search(self, state: WebSearchState) -> Command:
        """検索を実行するノード"""
        try:
            task = state.get("task")
            if not task:
                raise ValueError("taskがステートに存在しません")

            queries = state.get("queries")
            if not queries:
                raise ValueError("queriesがステートに存在しません")

            for query in queries:
                search_results = await self.search_client.search(query)
                task.add_web_search_attempt(query=query, results=search_results)

            return Command(update={}, goto="generate_task_result")

        except Exception as e:
            logger.error(f"検索実行でエラーが発生しました: {e!s}", exc_info=True)
            raise

    async def generate_task_result(self, state: WebSearchState) -> Command:
        """タスク結果を生成するノード"""
        try:
            task = state.get("task")
            if not task:
                raise ValueError("taskがステートに存在しません")

            attempt = state.get("attempt", 0)
            feedback = state.get("feedback")

            previous_result = task.result if attempt > 0 else None
            await self.task_result_service.execute(
                task, feedback=feedback, previous_result=previous_result
            )

            logger.info(f"タスク結果生成完了: attempt={attempt + 1}")

            return Command(update={}, goto="evaluate_task_result")

        except Exception as e:
            logger.error(f"タスク結果生成でエラーが発生しました: {e!s}", exc_info=True)
            raise

    async def evaluate_task_result(self, state: WebSearchState) -> Command:
        """タスク結果を評価し、改善が必要か判断するノード"""
        try:
            task = state.get("task")
            if not task:
                raise ValueError("taskがステートに存在しません")

            attempt = state.get("attempt", 0)

            evaluation = await self.task_evaluation_service.execute(task)

            if evaluation.is_satisfactory or attempt >= self.MAX_ATTEMPTS - 1:
                logger.info(
                    f"Web検索タスク完了: attempt={attempt + 1}, satisfactory={evaluation.is_satisfactory}"
                )
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

        except Exception as e:
            logger.error(f"タスク結果評価でエラーが発生しました: {e!s}", exc_info=True)
            raise

    def build_graph(self) -> StateGraph:
        graph = StateGraph(WebSearchState)

        graph.add_node("generate_search_queries", self.generate_search_queries)
        graph.add_node("execute_search", self.execute_search)
        graph.add_node("generate_task_result", self.generate_task_result)
        graph.add_node("evaluate_task_result", self.evaluate_task_result)

        graph.set_entry_point("generate_search_queries")

        return graph.compile()  # type: ignore
