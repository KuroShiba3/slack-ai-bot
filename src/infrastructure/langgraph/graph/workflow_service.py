import asyncio
from typing import TypedDict

from langgraph.graph import StateGraph

from ...domain.model import TaskPlan, Conversation, WorkflowResult
from ...domain.service.agent_workflow_service import AgentWorkflowService
from ...log.logger import get_logger

logger = get_logger(__name__)

class Context(TypedDict):
    channel_id: str
    thread_ts: str
    message_ts: str
    user_id: str

class BaseState(TypedDict):
    conversation: Conversation
    context: Context
    task_plan: TaskPlan | None
    answer: str | None

class LangGraphWorkflowService(AgentWorkflowService):
    _graph = None
    _graph_lock = asyncio.Lock()
    _checkpointer_lock = asyncio.Lock()
    _graph_semaphore = asyncio.Semaphore(60)

    def __init__(self, state: BaseState):
        self._state = state

    async def _get_graph(self) -> StateGraph:
        if self._graph is None:
            async with self._graph_lock:
                if self._graph is None:
                    self._graph = await self._build_graph(self._state)
        return self._graph

    async def execute(self, conversation: Conversation, context: dict) -> WorkflowResult:
        async with self._graph_semaphore:
            try:
                initial_state = {
                    "conversation": conversation,
                    "context": context
                }

                graph = await self._get_graph()
                result = await graph.ainvoke(
                    initial_state,
                    {"configurable": {"thread_id": context.get("thread_id", "")}}
                )

                answer = result.get("answer", "")
                task_plan = result.get("task_plan")

                if not task_plan:
                    raise ValueError("タスク計画が生成されませんでした")

                return WorkflowResult(answer=answer, task_plan=task_plan)

            except Exception as e:
                logger.error(f"ワークフロー実行中にエラーが発生しました: {e}")
                raise

    async def build_graph(self, state: BaseState) -> StateGraph:
        """LangGraphのグラフを構築"""

        graph = StateGraph(state)

        return graph.compile()
