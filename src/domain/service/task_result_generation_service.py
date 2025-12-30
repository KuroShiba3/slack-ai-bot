from ...domain.service.port import LLMClient
from ..model import Message, SearchResult, Task, TaskStatus, WebSearchTaskLog


class TaskResultGenerationService:
    """検索結果からタスク結果を生成するサービス"""

    SYSTEM_PROMPT = """あなたはタスク実行エージェントです。以下の検索結果を元に、割り当てられたタスクの結果をまとめてください。

## システムアーキテクチャの理解:
1. **タスク計画**: ユーザーの質問を複数のタスクに分割
2. **タスク実行(あなたの役割)**: 各タスクについて検索を実行し、結果をまとめる
3. **回答生成**: すべてのタスク結果を統合してユーザーに最終回答を提示

**重要**: 回答生成エージェントは検索結果を直接見ることができません。

## タスク結果作成のルール:

1. **検索結果のみを使用**:
    - 検索結果に含まれる情報のみを使用
    - 推測しない

2. **次のエージェントが理解できる内容**:
    - 数字、日付、固有名詞など具体的な情報を含める
    - 専門用語は簡潔に補足

3. **情報源の記載(必須)**:
    - 引用番号: [0], [1] のように角括弧で囲む
    - Slackリンク形式: `<URL|表示名>`
    - **URLは一字一句完全にコピー(変更・創作厳禁)**

4. **フォーマット**:
    ```
    (タスク結果の本文)[0][1]

    【参考情報】(2件)
    [0] <URL|表示名>
    [1] <URL|表示名>
    ```"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(
        self,
        task: Task,
        feedback: str | None = None,
        previous_result: str | None = None,
    ):
        """検索結果からタスク結果を生成し、タスクを完了させる"""
        search_results = self._get_search_results_from_task(task)

        human_prompt = self._build_human_prompt(
            task_description=task.description,
            search_results=search_results,
            feedback=feedback,
            previous_result=previous_result,
        )

        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            Message.create_user_message(human_prompt),
        ]

        task_result = await self.llm_client.generate(messages)

        if task.status == TaskStatus.PENDING:
            task.complete(task_result)
        if task.status == TaskStatus.COMPLETED:
            task.update_result(task_result)

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
        search_results: list[SearchResult],
        feedback: str | None,
        previous_result: str | None,
    ) -> str:
        """ヒューマンプロンプトを構築する"""
        current_date = self._get_current_date()

        search_results_section = ""
        if search_results:
            results_parts = ["\n## 取得した検索結果:"]
            for i, result in enumerate(search_results, 1):
                results_parts.append(f"\n### 検索結果 {i}")
                results_parts.append(f"\n**タイトル**: {result.title}")
                results_parts.append(f"\n**URL**: {result.url}")
                results_parts.append(f"\n**内容**:\n{result.content}\n")
            results_parts.append(
                "\n**【重要】URLを【参考情報】に含める場合は、一字一句完全にコピーしてください。**"
            )
            search_results_section = "".join(results_parts)

        feedback_section = ""
        if feedback:
            feedback_parts = [f"\n## 改善フィードバック:\n{feedback}"]
            if previous_result:
                feedback_parts.append(f"\n## 以前のタスク結果:\n{previous_result}")
            feedback_parts.append(
                "\n**重要**: フィードバックを参考にして、より良いタスク結果を作成してください。"
            )
            feedback_section = "".join(feedback_parts)

        return f"""## 現在の日付:
{current_date}

## 割り当てられたタスク:
{task_description}{search_results_section}{feedback_section}"""
