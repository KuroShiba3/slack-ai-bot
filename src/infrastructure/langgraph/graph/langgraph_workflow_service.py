import asyncio

from langgraph.graph import StateGraph

from src.infrastructure.exception.config_exception import MissingEnvironmentVariableError

from ....config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from ....domain.model import ChatSession, WorkflowResult
from ....domain.service import (
    AnswerGenerationService,
    GeneralAnswerService,
    SearchQueryGenerationService,
    TaskPlanningService,
    TaskResultEvaluationService,
    TaskResultGenerationService,
)
from ....log import get_logger
from ...external.llm import LangChainLLMClient, ModelFactory
from ...external.web_search import GoogleSearchClient
from ..agents import GeneralAnswerAgent, SupervisorAgent, WebSearchAgent
from .state import BaseState

logger = get_logger(__name__)


class LangGraphWorkflowService:
    _graph = None
    _graph_lock = asyncio.Lock()
    _graph_semaphore = asyncio.Semaphore(60)

    def __init__(self, model_factory: ModelFactory):
        self._model_factory = model_factory

        gemini_2_0_flash_client = LangChainLLMClient(
            model_factory=model_factory, model_name="gemini-2.0-flash"
        )

        gemini_2_5_flash_client = LangChainLLMClient(
            model_factory=model_factory, model_name="gemini-2.5-flash"
        )

        missing_vars = []
        if not GOOGLE_API_KEY:
            missing_vars.append("GOOGLE_API_KEY")
        if not GOOGLE_CSE_ID:
            missing_vars.append("GOOGLE_CSE_ID")
        if missing_vars:
            raise MissingEnvironmentVariableError(missing_vars)

        search_client = GoogleSearchClient(
            google_api_key=GOOGLE_API_KEY, google_cse_id=GOOGLE_CSE_ID
        )

        task_planning_service = TaskPlanningService(gemini_2_5_flash_client)
        general_answer_service = GeneralAnswerService(gemini_2_0_flash_client)
        search_query_service = SearchQueryGenerationService(gemini_2_0_flash_client)
        task_result_service = TaskResultGenerationService(gemini_2_0_flash_client)
        task_evaluation_service = TaskResultEvaluationService(gemini_2_5_flash_client)
        answer_generation_service = AnswerGenerationService(gemini_2_5_flash_client)

        self.supervisor_agent = SupervisorAgent(
            task_planning_service=task_planning_service,
            answer_generation_service=answer_generation_service,
        )

        self.web_search_agent = WebSearchAgent(
            search_query_service=search_query_service,
            task_result_service=task_result_service,
            task_evaluation_service=task_evaluation_service,
            search_client=search_client,
        )

        self.general_answer_agent = GeneralAnswerAgent(
            general_answer_service=general_answer_service
        )

    async def _get_graph(self) -> StateGraph:
        if self._graph is None:
            async with self._graph_lock:
                if self._graph is None:
                    self._graph = self.build_graph()
        return self._graph

    async def execute(self, chat_session: ChatSession, context: dict) -> WorkflowResult:
        async with self._graph_semaphore:
            initial_state = {"chat_session": chat_session, "context": context}
            graph = await self._get_graph()
            result = await graph.ainvoke(  # type: ignore
                initial_state
            )
            answer = result.get("answer", "")
            task_plan = result.get("task_plan")

            return WorkflowResult(answer=answer, task_plan=task_plan)

    def build_graph(self) -> StateGraph:
        """LangGraphのグラフを構築"""
        graph = StateGraph(BaseState)

        graph.add_node("plan_tasks", self.supervisor_agent.plan_tasks)
        graph.add_node(
            "generate_final_answer", self.supervisor_agent.generate_final_answer
        )

        graph.add_node("general_answer", self.general_answer_agent.build_graph())  # type: ignore
        graph.add_node("web_search", self.web_search_agent.build_graph())  # type: ignore

        graph.set_entry_point("plan_tasks")

        graph.add_edge("general_answer", "generate_final_answer")
        graph.add_edge("web_search", "generate_final_answer")

        return graph.compile()  # type: ignore
