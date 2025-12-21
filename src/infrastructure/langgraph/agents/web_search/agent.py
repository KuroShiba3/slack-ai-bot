import asyncio
import re
from typing import Optional, Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_community import GoogleSearchAPIWrapper
from langgraph.types import Command, Send
from langgraph.graph import StateGraph, END

from .....domain.model import WebSearchTaskLog, Task, SearchResult, TaskPlan
from ....llm import ModelFactory
from ....slack import SlackMessageService
from .....log import get_logger
from ...graph.state import BaseState
from .prompts import (
    get_search_query_system,
    get_search_query_human,
    get_task_result_system,
    get_task_result_human,
    get_evaluate_task_result_system,
    get_evaluate_task_result_human
)

logger = get_logger(__name__)


class PrivateState(TypedDict, total=False):
    feedback: Optional[str]
    attempt: int
    task_id: str
    query: str
    task_plan: TaskPlan


class WebSearchState(BaseState, PrivateState):
    pass


class WebSearchAgent:
    def __init__(self,
                model_factory: ModelFactory,
                slack_service: SlackMessageService,
                google_api_key: str,
                google_cse_id: str):
        self._model_factory = model_factory
        self._slack_service = slack_service
        self._google_api_key = google_api_key
        self._google_cse_id = google_cse_id

    def _get_task_from_state(self, state: WebSearchState, task_id: str) -> Task:
        """stateのtask_planから指定されたIDのタスクを取得"""
        task_plan = state.get("task_plan")
        if not task_plan:
            raise ValueError("task_planがステートに存在しません")

        for task in task_plan.tasks:
            if str(task.id) == task_id:
                return task

        raise ValueError(f"task_id={task_id}のタスクが見つかりません")

    async def generate_search_queries(self, state: WebSearchState, config: RunnableConfig | None = None) -> Command:

        # configからノード固有のmodel_nameを取得（フォールバックあり）
        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("generate_search_queries_model", configurable.get("default_model", "gemini-2.0-flash"))

        class SearchQueries(BaseModel):
            queries: list[str] = Field(description="生成された検索クエリのリスト（最大3個）", max_length=3)
            reason: str = Field(description="これらのクエリを選んだ理由")

        # Sendから渡されるtask_idを取得
        task_id = state.get("task_id")
        if not task_id:
            raise ValueError("task_idがステートに存在しません")

        # タスクを取得
        task = self._get_task_from_state(state, task_id)
        task_description = task.description

        # タスクログから以前の検索クエリとフィードバックを取得
        previous_queries = []
        feedback = state.get("feedback")

        if isinstance(task.task_log, WebSearchTaskLog):
            previous_queries = task.task_log.get_all_queries()

        system_message = SystemMessage(content=get_search_query_system())
        human_message = HumanMessage(content=get_search_query_human(
            task_description,
            previous_queries,
            feedback
        ))

        try:
            model = self._model_factory.create(model_name)
            search_queries_result = await model.with_structured_output(SearchQueries).ainvoke(
                [system_message, human_message]
            )

            if not search_queries_result.queries:
                logger.warning("generate_search_queriesでクエリが生成されませんでした")
                task.fail("適切な検索クエリを生成できませんでした。")

                # task_planはミュータブルなので、updateで返す必要はない
                return Command(update={}, goto=END)

            # SendにBaseStateの全フィールドを含める
            sends = [
                Send("execute_search", {
                    "query": query,
                    "task_id": task_id,
                    "chat_session": state.get("chat_session"),
                    "context": state.get("context"),
                    "task_plan": state.get("task_plan"),
                    "answer": state.get("answer"),
                    "feedback": state.get("feedback"),
                    "attempt": state.get("attempt", 0)
                })
                for query in search_queries_result.queries
            ]

            return Command(update={}, goto=sends)

        except Exception as e:
            logger.error(f"generate_search_queriesでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def execute_search(self, state: WebSearchState) -> Command:
        # Sendから呼ばれる場合、stateにqueryとtask_idが含まれる
        query = state.get("query")
        task_id = state.get("task_id")

        def clean_text(text: str) -> str:
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            return '\n'.join(lines)

        if not query or not task_id:
            return Command(update={}, goto="generate_task_result")

        # タスクを取得
        task = self._get_task_from_state(state, task_id)

        try:
            search = GoogleSearchAPIWrapper(
                google_api_key=self._google_api_key,
                google_cse_id=self._google_cse_id
            )

            results = search.results(query, num_results=3)

            if not results:
                return Command(update={}, goto="generate_task_result")

            search_results: list[SearchResult] = []
            for result in results:
                url = result['link']
                title = result['title']
                snippet = result.get('snippet', '')

                try:
                    loader = WebBaseLoader(url)
                    load_task = asyncio.to_thread(loader.load)
                    docs = await asyncio.wait_for(load_task, timeout=8.0)

                    raw_content = docs[0].page_content
                    cleaned_content = clean_text(raw_content)
                    content = cleaned_content[:5000]

                    search_results.append(SearchResult(
                        url=url,
                        title=title,
                        content=content
                    ))
                except Exception as e:
                    logger.warning(f"Webページ取得エラー: {str(e)}")
                    search_results.append(SearchResult(
                        url=url,
                        title=title,
                        content=snippet
                    ))

            # タスクログに検索結果を追加
            if search_results:
                task.add_log_attempt(query=query, results=search_results)

            # task_planはミュータブルなので、updateで返す必要はない
            return Command(update={}, goto="generate_task_result")

        except Exception as e:
            logger.error(f"execute_searchでエラーが発生しました: {str(e)}", exc_info=True)
            return Command(update={}, goto="generate_task_result")

    async def generate_task_result(self, state: WebSearchState, config: RunnableConfig | None = None) -> Command:

        # configからノード固有のmodel_nameを取得（フォールバックあり）
        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("generate_task_result_model", configurable.get("default_model", "gemini-2.0-flash"))

        # task_idを取得
        task_id = state.get("task_id")
        if not task_id:
            raise ValueError("task_idがステートに存在しません")

        # タスクを取得
        task = self._get_task_from_state(state, task_id)

        # タスクログから検索結果を取得
        search_results = []
        if isinstance(task.task_log, WebSearchTaskLog):
            # タスクログから全ての検索結果を取得
            for attempt in task.task_log.attempts:
                if attempt.results:
                    for result in attempt.results:
                        # SearchResultを辞書形式に変換してプロンプトに渡す
                        search_results.append({
                            "url": result.url,
                            "title": result.title,
                            "content": result.content
                        })

        system_message = SystemMessage(content=get_task_result_system())
        human_message = HumanMessage(content=get_task_result_human(
            task.description,
            search_results
        ))

        try:
            model = self._model_factory.create(model_name)
            answer = await model.ainvoke([system_message, human_message])

            # タスクを完了
            task.complete(answer.content)

            # task_planはミュータブルなので、updateで返す必要はない
            return Command(update={}, goto="evaluate_task_result")

        except Exception as e:
            logger.error(f"generate_task_resultでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def evaluate_task_result(self, state: WebSearchState, config: RunnableConfig | None = None) -> Command:
        # configからノード固有のmodel_nameを取得（フォールバックあり）
        if config is None:
            config = {}
        configurable = config.get("configurable", {})
        model_name = configurable.get("evaluate_task_result_model", configurable.get("default_model", "gemini-2.0-flash"))

        class TaskEvaluation(BaseModel):
            is_satisfactory: bool = Field(description="タスク結果が十分か")
            need: Optional[Literal["search", "generate"]] = Field(description="改善が必要な場合の種類")
            reason: str = Field(description="判断理由")
            feedback: Optional[str] = Field(description="改善のためのフィードバック")

        # task_idを取得
        task_id = state.get("task_id")
        if not task_id:
            raise ValueError("task_idがステートに存在しません")

        # タスクを取得
        task = self._get_task_from_state(state, task_id)

        if not task.result:
            return Command(update={}, goto=END)

        # タスクログから検索結果を取得
        search_results = []
        if isinstance(task.task_log, WebSearchTaskLog):
            for attempt in task.task_log.attempts:
                search_results.extend(attempt.results)

        attempt = state.get("attempt", 0) + 1

        system_message = SystemMessage(content=get_evaluate_task_result_system())
        human_message = HumanMessage(content=get_evaluate_task_result_human(
            task_description=task.description,
            task_result=task.result,
            search_results=search_results
        ))

        try:
            model = self._model_factory.create(model_name)
            evaluation = await model.with_structured_output(TaskEvaluation).ainvoke(
                [system_message, human_message]
            )

            if evaluation.is_satisfactory or attempt >= 2:
                return Command(update={}, goto=END)

            if evaluation.need == "search":
                return Command(
                    update={"attempt": attempt, "feedback": evaluation.feedback},
                    goto="generate_search_queries"
                )
            elif evaluation.need == "generate":
                return Command(
                    update={"attempt": attempt, "feedback": evaluation.feedback},
                    goto="generate_task_result"
                )
            else:
                return Command(update={}, goto=END)

        except Exception as e:
            logger.error(f"evaluate_task_resultでエラーが発生しました: {str(e)}", exc_info=True)
            return Command(update={}, goto=END)

    def build_graph(self) -> StateGraph:
        """Web検索エージェントのグラフを構築"""
        graph = StateGraph(WebSearchState)

        graph.add_node("generate_search_queries", self.generate_search_queries)
        graph.add_node("execute_search", self.execute_search)
        graph.add_node("generate_task_result", self.generate_task_result)
        graph.add_node("evaluate_task_result", self.evaluate_task_result)

        graph.set_entry_point("generate_search_queries")

        return graph.compile()