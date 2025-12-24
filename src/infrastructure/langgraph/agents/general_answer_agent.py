from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Command

from ....domain.model import Task
from ....domain.service import GeneralAnswerService
from ....log import get_logger
from ..graph.state import BaseState

logger = get_logger(__name__)


class GeneralAnswerPrivateState(TypedDict):
    """GeneralAnswerAgent専用のプライベートステートフィールド"""
    task: Task  # 親グラフから渡される


class GeneralAnswerState(BaseState, GeneralAnswerPrivateState):
    """GeneralAnswerAgent用の完全なステート（BaseState + プライベートフィールド）"""
    pass


class GeneralAnswerAgent:
    """一般回答エージェント: 一般的な質問への回答を担当"""

    def __init__(self, general_answer_service: GeneralAnswerService):
        self.general_answer_service = general_answer_service

    async def generate_answer(self, state: GeneralAnswerState) -> Command:
        """一般回答を生成するノード"""
        try:
            task = state.get("task")
            if not task:
                raise ValueError("taskがステートに存在しません")

            chat_session = state.get("chat_session")
            if not chat_session:
                raise ValueError("chat_sessionがステートに存在しません")

            # タスクを実行
            await self.general_answer_service.execute(chat_session, task)

            logger.info(f"一般回答タスク完了: task_id={task.id}")

            return Command(update={}, goto=END)

        except Exception as e:
            logger.error(f"一般回答生成でエラーが発生しました: {e!s}", exc_info=True)
            raise

    def build_graph(self) -> StateGraph:
        """GeneralAnswerエージェントのサブグラフを構築"""
        graph = StateGraph(GeneralAnswerState)

        # ノードを追加
        graph.add_node("generate_answer", self.generate_answer)

        # エントリーポイント
        graph.set_entry_point("generate_answer")

        return graph.compile()
