from datetime import datetime
from pydantic import BaseModel, Field

from ..model import Task, WebSearchTaskLog, Message
from ..llm_client import LLMClient


class SearchQueryGenerationService:
    """検索クエリを生成するサービス"""

    SYSTEM_PROMPT = """あなたは検索クエリ生成の専門家です。割り当てられたタスクに答えるために最適な検索クエリを生成してください。

## クエリ生成のルール:

1. **複数の視点から検索**:
    - 異なる角度から情報を集めるため、2-3個のクエリを生成
    - 重複する内容のクエリは避ける

2. **具体的で明確なクエリ**:
    - 曖昧な表現を避け、固有名詞を使う

3. **時間的文脈の考慮**:
    - 「今日」「本日」を含む場合 → 必ず日付を含める
    - 最新情報が必要な場合 → "最新"や年月を含める

4. **タスク内容の活用**:
    - 代名詞は具体的な名詞に変換
    - 文脈から暗黙の情報を補完

## 重要な注意事項:
- 必ず2個以上のクエリを生成してください
- 前回のクエリと異なる角度からの検索を心がけてください"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(
        self,
        task: Task,
        feedback: str | None = None
    ) -> list[str]:
        """タスクから検索クエリを生成する

        Args:
            task: 検索対象のタスク
            feedback: 改善のためのフィードバック（オプション）

        Returns:
            生成された検索クエリのリスト（最大3個）
        """
        # Pydanticモデルを定義
        class _SearchQueries(BaseModel):
            queries: list[str] = Field(description="生成された検索クエリのリスト（最大3個）", max_length=3)
            reason: str = Field(description="これらのクエリを選んだ理由")

        # タスクログから以前の検索クエリを取得
        previous_queries = []
        if isinstance(task.task_log, WebSearchTaskLog):
            previous_queries = task.task_log.get_all_queries()

        # ヒューマンプロンプトを構築
        human_prompt = self._build_human_prompt(
            task_description=task.description,
            previous_queries=previous_queries,
            feedback=feedback
        )

        # メッセージリストを構築
        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            Message.create_user_message(human_prompt)
        ]

        # LLMで検索クエリを生成
        search_queries_result = await self.llm_client.generate_with_structured_output(
            messages,
            _SearchQueries
        )

        return search_queries_result.queries

    def _get_current_date(self) -> str:
        """現在の日付を取得する"""
        return datetime.now().strftime("%Y年%m月%d日")

    def _build_human_prompt(
        self,
        task_description: str,
        previous_queries: list[str],
        feedback: str | None
    ) -> str:
        """ヒューマンプロンプトを構築する"""
        current_date = self._get_current_date()

        # 過去のクエリセクション
        previous_queries_section = ""
        if previous_queries:
            queries_text = "\n".join([f"- {q}" for q in previous_queries])
            previous_queries_section = f"""
## すでに利用した検索クエリ:
{queries_text}

**重要**: 前回の検索で十分な結果が得られなかったため、異なる角度からの新しいクエリを生成してください。"""

        # フィードバックセクション
        feedback_section = ""
        if feedback:
            feedback_section = f"""

## 改善フィードバック:
{feedback}

上記のフィードバックを参考にしてください。"""

        return f"""## 現在の日付:
{current_date}

## 割り当てられたタスク:
{task_description}{previous_queries_section}{feedback_section}"""
