import asyncio
from typing import Any, Annotated, TypedDict, Literal, Optional, Union

from langchain_core.messages import HumanMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph

from ...config import POSTGRES_URL
from ...domain.model import FinalAnswer
from ...domain.service.agent_workflow_service import AgentWorkflowService
from ...log.logger import get_logger

logger = get_logger(__name__)

class Context(TypedDict):
    channel_id: str
    thread_ts: str
    message_ts: str
    user_id: str

class SearchResult(TypedDict):
    url: str
    title: str
    content: str

class SearchAttemptDict(TypedDict):
    query: str
    results: list[SearchResult]

class WebSearchTaskLog(TypedDict):
    type: Literal["web_search"]
    attempts: list[SearchAttemptDict]

class GenerationAttempt(TypedDict):
    response: str

class GeneralAnswerTaskLog(TypedDict):
    type: Literal["general_answer"]
    attempts: list[GenerationAttempt]

TaskLog = Union[WebSearchTaskLog, GeneralAnswerTaskLog]

class Task(TypedDict):
    id: str
    description: str
    agent_name: str
    status: str
    result: Optional[str]
    task_log: TaskLog
    created_at: str
    completed_at: Optional[str]

class BaseState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    context: Context
    tasks: list[Task]
    final_answer: str | None

class LangGraphWorkflowService(AgentWorkflowService):
    _graph = None
    _checkpointer = None
    _checkpointer_cm = None
    _graph_lock = asyncio.Lock()
    _checkpointer_lock = asyncio.Lock()
    _graph_semaphore = asyncio.Semaphore(60)

    def __init__(self, state: BaseState):
        self._state = state

    @classmethod
    async def _get_checkpointer(cls):
        if cls._checkpointer is not None:
            try:
                if hasattr(cls._checkpointer, "conn") and cls._checkpointer.conn.closed:
                    cls._checkpointer = None
                    cls._checkpointer_cm = None
            except Exception:
                cls._checkpointer = None
                cls._checkpointer_cm = None

        if cls._checkpointer is None:
            async with cls._checkpointer_lock:
                if cls._checkpointer is None:
                    cls._checkpointer_cm = AsyncPostgresSaver.from_conn_string(POSTGRES_URL)
                    cls._checkpointer = await cls._checkpointer_cm.__aenter__()
                    await cls._checkpointer.setup()

        return cls._checkpointer

    @classmethod
    async def _get_graph(cls):
        if cls._graph is None:
            async with cls._graph_lock:
                if cls._graph is None:
                    cls._graph = await cls._build_graph()
        return cls._graph

    async def execute(self, user_message: str, context: dict[str, Any]) -> FinalAnswer:
        async with self._graph_semaphore:
            try:
                initial_state = {
                    "messages": [HumanMessage(content=user_message)],
                    "context": context
                }

                graph = await self._get_graph()
                result = await graph.ainvoke(
                    initial_state,
                    {"configurable": {"thread_id": context.get("thread_id", "")}}
                )
                return FinalAnswer(result.get("final_answer", ""))

            except Exception as e:
                logger.error(f"ワークフロー実行中にエラーが発生しました: {e}")
                raise

    async def build_graph(self):
        """LangGraphのグラフを構築"""

        checkpointer = await self._get_checkpointer()

        graph = StateGraph(self._state)

        return graph.compile(checkpointer=checkpointer)
