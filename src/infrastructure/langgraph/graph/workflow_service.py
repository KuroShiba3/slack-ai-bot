import asyncio

from langgraph.graph import StateGraph

from ....domain.model import ChatSession, WorkflowResult
from ....domain.service.workflow_service import IWorkflowService
from ....log import get_logger
from ....config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from ...llm import ModelFactory
from ...slack import SlackMessageService
from ..agents.supervisor.agent import SupervisorAgent
from ..agents.general_answer.agent import GeneralAnswerAgent
from ..agents.web_search.agent import WebSearchAgent

logger = get_logger(__name__)

class LangGraphWorkflowService(IWorkflowService):
    _graph = None
    _graph_lock = asyncio.Lock()
    _checkpointer_lock = asyncio.Lock()
    _graph_semaphore = asyncio.Semaphore(60)

    def __init__(
        self,
        model_factory: ModelFactory,
        slack_service: SlackMessageService,
        model_name: str = "gemini-2.0-flash"
    ):
        self._model_factory = model_factory
        self._slack_service = slack_service
        self._model_name = model_name

    async def _get_graph(self) -> StateGraph:
        if self._graph is None:
            async with self._graph_lock:
                if self._graph is None:
                    self._graph = self.build_graph()
        return self._graph

    async def execute(self, chat_session: ChatSession, context: dict) -> WorkflowResult:
        async with self._graph_semaphore:
            try:
                initial_state = {
                    "chat_session": chat_session,
                    "context": context
                }
                graph = await self._get_graph()
                result = await graph.ainvoke(
                    initial_state,
                    {
                        "configurable": {
                            "thread_id": context.get("thread_id", ""),
                            "default_model": self._model_name
                        }
                    }
                )
                answer = result.get("answer", "")
                task_plan = result.get("task_plan")

                if not task_plan:
                    raise ValueError("タスク計画が生成されませんでした")

                return WorkflowResult(answer=answer, task_plan=task_plan)

            except Exception as e:
                logger.error(f"ワークフロー実行中にエラーが発生しました: {e}")
                raise

    def build_graph(self) -> StateGraph:
        """LangGraphのグラフを構築"""

        supervisor_agent = SupervisorAgent(self._model_factory)
        general_answer_agent = GeneralAnswerAgent(self._model_factory)
        web_search_agent = WebSearchAgent(
            model_factory=self._model_factory,
            slack_service=self._slack_service,
            google_api_key=GOOGLE_API_KEY,
            google_cse_id=GOOGLE_CSE_ID
        )

        general_answer_graph = general_answer_agent.build_graph()
        web_search_graph = web_search_agent.build_graph()

        graph = supervisor_agent.build_graph(
            general_answer_graph=general_answer_graph,
            web_search_graph=web_search_graph
        )

        return graph
