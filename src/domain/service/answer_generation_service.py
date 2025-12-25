from ...domain.service.port import LLMClient
from ..model import ChatSession, Message, TaskPlan


class AnswerGenerationService:
    """タスク実行結果から最終回答を生成するサービス"""
    SYSTEM_PROMPT = """複数のタスクの実行結果を統合し、ユーザーの質問に対する包括的で分かりやすい回答を生成してください。

# 回答のルール:

1. **統合と一貫性**:
    - タスク結果を自然な文章として統合
    - 矛盾がある場合は両方の情報を提示

2. **簡潔さと適切な情報量**:
    - 質問の範囲内で重要な情報を過不足なく提供
    - 見出しは最小限(サブセクション「###」は使用しない)

3. **わかりやすさ**:
    - 簡潔で分かりやすい日本語
    - 箇条書きは3〜5項目程度に抑える

4. **Slack mrkdwn形式(厳守)**:
    - 太字: `*テキスト*`
    - 箇条書き: `• `(ネストは `    • `)
    - 見出し記号(#)は使用しない

5. **情報源の記載(必須)**:
    - **URLやファイル名の創作・推測は絶対禁止**
    - タスク結果のURLをそのまま正確に使用
    - 引用番号: [0], [1] のように角括弧で囲む
    - 同じURLは1つにまとめる
    - Slackリンク形式: `<URL|表示名>`
"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(self, chat_session: ChatSession, task_plan: TaskPlan) -> Message:
        """タスク実行結果から最終回答を生成する"""
        latest_message = chat_session.last_user_message()
        if not latest_message:
            raise ValueError("最終回答を生成するにはユーザーメッセージが必要です")

        task_results_text = task_plan.format_task_results()

        human_prompt = self._build_human_prompt(
            user_question=latest_message.content, task_results=task_results_text
        )

        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            *chat_session.messages[:-1],
            Message.create_user_message(human_prompt),
        ]

        answer_content = await self.llm_client.generate(messages)

        return Message.create_assistant_message(answer_content)

    def _build_human_prompt(self, user_question: str, task_results: str) -> str:
        return f"""## ユーザーの質問:
{user_question}

## タスクの実行結果:
{task_results}

上記のタスク結果を統合して、ユーザーの質問に対する包括的な回答を生成してください。

**【重要】タスク結果に含まれる【参考情報】セクションのURLは、一字一句完全にコピーしてください。URLの文字を変更・間違えることは絶対禁止です。**"""
