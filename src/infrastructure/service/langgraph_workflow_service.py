import asyncio
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ...domain.service.agent_workflow_service import AgentWorkflowService
from ...domain.model.final_answer import FinalAnswer
from ...config import POSTGRES_URL
from ...log.logger import get_logger

logger = get_logger(__name__)

class LangGraphWorkflowService(AgentWorkflowService):
    _graph = None
    _checkpointer = None
    _checkpointer_cm = None
    _graph_lock = asyncio.Lock()
    _checkpointer_lock = asyncio.Lock()
    _graph_semaphore = asyncio.Semaphore(60)

    def __init__(self):
        pass

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
    async def _build_graph(cls):
        """LangGraphのグラフを構築"""
        # TODO: 実際のLangGraph実装
        # from langgraph.graph import StateGraph, END
        #
        # checkpointer = await cls._get_checkpointer()
        #
        # workflow = StateGraph(State)
        # workflow.add_node("plan", cls._plan_node)
        # workflow.add_node("execute_web_search", cls._execute_web_search_node)
        # workflow.add_node("execute_general_answer", cls._execute_general_answer_node)
        # workflow.add_node("evaluate", cls._evaluate_node)
        # workflow.add_node("aggregate", cls._aggregate_node)
        #
        # # エッジの定義
        # workflow.add_edge("plan", ["execute_web_search", "execute_general_answer"])
        # workflow.add_edge(["execute_web_search", "execute_general_answer"], "evaluate")
        # workflow.add_conditional_edges(
        #     "evaluate",
        #     cls._should_retry,
        #     {
        #         "retry": "plan",
        #         "continue": "aggregate"
        #     }
        # )
        # workflow.add_edge("aggregate", END)
        #
        # return workflow.compile(checkpointer=checkpointer)
        pass

    @classmethod
    async def _get_graph(cls):
        if cls._graph is None:
            async with cls._graph_lock:
                if cls._graph is None:
                    cls._graph = await cls._build_graph()
        return cls._graph

    async def execute(self, user_message: str, context: Dict[str, Any]) -> FinalAnswer:
        async with self._graph_semaphore:
            try:
                graph = await self._get_graph()
                result = await graph.ainvoke(
                    {
                        "messages": [HumanMessage(content=user_message)],
                        "context": context or {}
                    },
                    {"configurable": {"thread_id": context.get("thread_id", "")}}
                )
                return FinalAnswer(result.get("final_answer", ""))

            except Exception as e:
                logger.error(f"ワークフロー実行中にエラーが発生しました: {e}")
                raise