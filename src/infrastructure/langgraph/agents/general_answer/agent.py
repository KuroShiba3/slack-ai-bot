from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import StateGraph, END

from ....llm import ModelFactory
from .....log import get_logger
from .....domain.model import Task, TaskPlan
from ...graph.state import BaseState
from ...utils.message_converter import MessageConverter
from .prompts import get_general_answer_system

logger = get_logger(__name__)


class PrivateState(TypedDict, total=False):
    """GeneralAnswerエージェント専用のプライベートステート"""
    task_id: str
    task_plan: TaskPlan


class GeneralAnswerState(BaseState, PrivateState):
    """GeneralAnswerエージェントが使用するステート（BaseState + PrivateState）"""
    pass


class GeneralAnswerAgent:
    def __init__(self, model_factory: ModelFactory):
        self._model_factory = model_factory

    def _get_task_from_state(self, state: GeneralAnswerState, task_id: str) -> Task:
        """stateのtask_planから指定されたIDのタスクを取得"""
        task_plan = state.get("task_plan")
        if not task_plan:
            raise ValueError("task_planがステートに存在しません")

        for task in task_plan.tasks:
            if str(task.id) == task_id:
                return task

        raise ValueError(f"task_id={task_id}のタスクが見つかりません")

    async def execute_task(self, state: GeneralAnswerState, config: RunnableConfig | None = None) -> Command:
        """タスクを実行して結果を返す"""

        # configからノード固有のmodel_nameを取得（フォールバックあり）
        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("execute_task_model", configurable.get("default_model", "gemini-2.0-flash"))

        # task_idを取得
        task_id = state.get("task_id")
        if not task_id:
            raise ValueError("task_idがステートに存在しません")

        # タスクを取得
        task = self._get_task_from_state(state, task_id)

        # チャットセッションを取得
        chat_session = state.get("chat_session")
        if not chat_session:
            raise ValueError("chat_sessionがステートに存在しません")

        try:
            # チャットセッションの履歴からLangChainメッセージに変換
            langchain_messages = MessageConverter.to_langchain_messages(chat_session.messages)

            # タスク用のプロンプトを構築
            system_message = SystemMessage(content=get_general_answer_system())
            task_message = HumanMessage(content=f"次のタスクについて回答してください: {task.description}")

            messages = [system_message] + langchain_messages + [task_message]

            # LLMで回答生成
            model = self._model_factory.create(model_name)
            response = await model.ainvoke(messages)

            # タスクログに生成試行を追加
            task.add_log_attempt(response=response.content)

            # タスクを完了
            task.complete(response.content)

            # 空のupdateで「ステートを変更しない」ことを明示
            # これにより並列実行時のステートマージ衝突を回避
            return Command(update={}, goto=END)

        except Exception as e:
            logger.error(f"Error in execute_task: {str(e)}", exc_info=True)

            # タスクを失敗状態に更新
            task.fail(str(e))

            # task_planを更新してステートに反映（エラー時も必要）
            task_plan = state.get("task_plan")
            if task_plan:
                # エラー情報を含めてステートを更新してから例外を投げる
                # ただし、LangGraphは例外が発生すると処理が中断されるため、
                # ここでのupdate反映は保証されない可能性がある
                pass

            raise

    def build_graph(self) -> StateGraph:
        """GeneralAnswerエージェントのグラフを構築"""
        graph = StateGraph(GeneralAnswerState)

        graph.add_node("execute_task", self.execute_task)

        graph.set_entry_point("execute_task")

        return graph.compile()