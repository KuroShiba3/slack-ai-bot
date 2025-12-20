import asyncio
import re
from typing import Type, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_community import GoogleSearchAPIWrapper
from langgraph.types import Command, Send, END

from .....domain.model import WebSearchTaskLog
from ...llm import ModelFactory
from ...slack import SlackMessageService
from .....config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from .....log import get_logger
from ...graph.workflow_service import BaseState
from .prompts import (
    get_search_query_system,
    get_search_query_human,
    get_task_result_system,
    get_task_result_human,
    get_evaluate_task_result_system
)

logger = get_logger(__name__)


class WebSearchAgent:
    def __init__(self,
                model_factory: ModelFactory,
                slack_service: SlackMessageService,
                state: BaseState,
                google_api_key: str,
                google_cse_id: str,
                task_service: Type[TaskStateService] = TaskStateService):
        self._model_factory = model_factory
        self._slack_service = slack_service
        self._state = state
        self._google_api_key = google_api_key
        self._google_cse_id = google_cse_id
        self._TaskService = task_service

        self._context = state.get("context")
        self._task_id = state.get("task_id")
        self._task_description = state.get("task_description")

    async def generate_search_queries(self, model_name: str) -> Command:

        class SearchQueries(BaseModel):
            queries: list[str] = Field(description="生成された検索クエリのリスト（最大3個）", max_length=3)
            reason: str = Field(description="これらのクエリを選んだ理由")

        task = self._TaskService.get_task_by_id(self._state, self._task_id)
        previous_queries = []
        feedback = None

        if task and task.log and isinstance(task.log, WebSearchTaskLog):
            previous_queries = task.log.get_all_queries()

        system_message = SystemMessage(content=get_search_query_system())
        human_message = HumanMessage(content=get_search_query_human(
            self._task_description,
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
                return Command(
                    update=self._TaskService.complete_task(
                        self._state,
                        self._task_id,
                        "適切な検索クエリを生成できませんでした。"
                    ),
                    goto=END
                )

            sends = [
                Send("execute_search", {"query": query, "task_id": self._task_id})
                for query in search_queries_result.queries
            ]

            return Command(
                update={
                    "search_queries": search_queries_result.queries,
                },
                goto=sends
            )

        except Exception as e:
            logger.error(f"generate_search_queriesでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def execute_search(self, config: dict) -> Command:
        # Sendから呼ばれる場合、stateにqueryとtask_idが含まれる
        query = config.get("query")
        task_id = config.get("task_id")

        def clean_text(text: str) -> str:
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            return '\n'.join(lines)

        if not query:
            return Command(update={"search_results": []})

        try:
            search = GoogleSearchAPIWrapper(
                google_api_key=self._google_api_key,
                google_cse_id=self._google_cse_id
            )

            results = search.results(query, num_results=3)

            if not results:
                return Command(update={"search_results": []})

            search_results = []
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

                    search_results.append({
                        "query": query,
                        "title": title,
                        "url": url,
                        "content": content
                    })
                except Exception as e:
                    logger.warning(f"Webページ取得エラー: {str(e)}")
                    search_results.append({
                        "query": query,
                        "title": title,
                        "url": url,
                        "content": snippet,
                    })

            # タスクログに検索結果を更新
            if task_id and search_results:
                task_update = self._TaskService.add_web_search_attempt(
                    self._state,
                    task_id,
                    query,
                    search_results
                )
                return Command(
                    update=task_update,
                    goto="generate_task_result"
                )

            return Command(
                goto="generate_task_result"
            )

        except Exception as e:
            logger.error(f"execute_searchでエラーが発生しました: {str(e)}", exc_info=True)
            return Command(
                goto="generate_task_result"
            )

    async def generate_task_result(self, model_name: str) -> Command:

        # タスクログから検索結果を直接取得
        search_results = []
        if self._task_id:
            task = self._TaskService.get_task_by_id(self._state, self._task_id)
            if task and task.log and isinstance(task.log, WebSearchTaskLog):
                # タスクログから全ての検索結果を取得
                for attempt in task.log.attempts:
                    if attempt.results:
                        for result in attempt.results:
                            # 辞書形式に変換（もし必要であれば）
                            if hasattr(result, 'to_dict'):
                                search_results.append(result.to_dict())
                            else:
                                search_results.append(result)

        system_message = SystemMessage(content=get_task_result_system())
        human_message = HumanMessage(content=get_task_result_human(
            self._task_description,
            search_results
        ))

        try:
            model = self._model_factory.create(model_name)
            answer = await model.ainvoke([system_message, human_message])

            updated_state = self._TaskService.complete_task(
                self._state,
                self._task_id,
                answer.content
            )

            return Command(
                update=updated_state,
                goto="evaluate_task_result"
            )

        except Exception as e:
            logger.error(f"generate_task_resultでエラーが発生しました: {str(e)}", exc_info=True)
            raise

    async def evaluate_task_result(self, model_name: str) -> Command:

        class TaskEvaluation(BaseModel):
            is_satisfactory: bool = Field(description="タスク結果が十分か")
            need: Optional[Literal["search", "generate"]] = Field(description="改善が必要な場合の種類")
            reason: str = Field(description="判断理由")
            feedback: Optional[str] = Field(description="改善のためのフィードバック")

        task = self._TaskService.get_task_by_id(self._state, self._task_id)
        if not task or not task.result:
            return Command(goto=END)

        search_results = self._state.get("search_results", [])
        attempt = self._state.get("attempt", 0) + 1

        human_parts = [
            f"## 割り当てられたタスク:\n{self._task_description}",
            f"\n## 生成されたタスク結果:\n{task.result}"
        ]

        if search_results:
            human_parts.append("\n## 取得した検索結果:")
            for i, result in enumerate(search_results, 1):
                human_parts.append(f"\n### 検索結果 {i}")
                human_parts.append(f"\n**URL**: {result.get('url', '')}")
                human_parts.append(f"\n**タイトル**: {result.get('title', '')}")

        system_message = SystemMessage(content=get_evaluate_task_result_system())
        human_message = HumanMessage(content="".join(human_parts))

        try:
            model = self._model_factory.create(model_name)
            evaluation = await model.with_structured_output(TaskEvaluation).ainvoke(
                [system_message, human_message]
            )

            if evaluation.is_satisfactory or attempt >= 2:
                return Command(goto=END)

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
                return Command(goto=END)

        except Exception as e:
            logger.error(f"evaluate_task_resultでエラーが発生しました: {str(e)}", exc_info=True)
            return Command(goto=END)