from typing import Literal

from pydantic import BaseModel, Field

from src.domain.exception.service_exception import TaskResultNotFoundError

from ...domain.service.port import LLMClient
from ..model import Message, SearchResult, Task, TaskEvaluation, WebSearchTaskLog


class TaskResultEvaluationService:
    """タスク結果の品質を評価するサービス"""

    SYSTEM_PROMPT = """あなたはタスク結果品質を評価する専門家です。

## 評価の流れ:

### 1. 検索結果の確認
**need = "search" (検索改善が必要):**
- 検索結果にタスクに答える情報が含まれていない
- 検索クエリが不適切

### 2. タスク結果の確認
**need = "generate" (タスク結果改善が必要):**
- 検索結果の重要情報が活用されていない
- 構成や表現が分かりにくい

### 3. 全体的な満足度
**need = None (改善不要):**
- 重要情報が適切に反映されている
- 自然な文章で構成されている

## 重要:
- is_satisfactory は need が None の場合のみ True
- feedback は具体的で実行可能な内容に"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(self, task: Task) -> TaskEvaluation:
        """タスク結果を評価する"""
        if not task.result:
            raise TaskResultNotFoundError()

        class _TaskEvaluationSchema(BaseModel):
            is_satisfactory: bool = Field(description="タスク結果が十分か")
            need: Literal["search", "generate"] | None = Field(
                description="改善が必要な場合の種類"
            )
            reason: str = Field(description="判断理由")
            feedback: str | None = Field(description="改善のためのフィードバック")

        search_results = self._get_search_results_from_task(task)

        human_prompt = self._build_human_prompt(
            task_description=task.description,
            task_result=task.result,
            search_results=search_results,
        )

        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            Message.create_user_message(human_prompt),
        ]

        evaluation = await self.llm_client.generate_with_structured_output(
            messages, _TaskEvaluationSchema
        )

        return TaskEvaluation(
            is_satisfactory=evaluation.is_satisfactory,
            need=evaluation.need,
            reason=evaluation.reason,
            feedback=evaluation.feedback,
        )

    def _get_search_results_from_task(self, task: Task) -> list[SearchResult]:
        """タスクログから検索結果を取得する"""
        search_results = []

        if isinstance(task.task_log, WebSearchTaskLog):
            for attempt in task.task_log.attempts:
                if attempt.results:
                    search_results.extend(attempt.results)

        return search_results

    def _get_current_date(self) -> str:
        from datetime import datetime

        return datetime.now().strftime("%Y年%m月%d日")

    def _build_human_prompt(
        self,
        task_description: str,
        task_result: str,
        search_results: list[SearchResult],
    ) -> str:
        """ヒューマンプロンプトを構築する"""
        current_date = self._get_current_date()

        search_results_section = ""
        if search_results:
            results_parts = ["\n## 取得した検索結果:"]
            for i, result in enumerate(search_results, 1):
                results_parts.append(f"\n### 検索結果 {i}")
                results_parts.append(f"\n**URL**: {result.url}")
                results_parts.append(f"\n**タイトル**: {result.title}")
            search_results_section = "".join(results_parts)

        return f"""## 現在の日付:
{current_date}

## 割り当てられたタスク:
{task_description}

## 生成されたタスク結果:
{task_result}{search_results_section}"""
