from datetime import datetime

from ..llm_client import LLMClient
from ..model import ChatSession, Message, Task


class GeneralAnswerService:
    """一般的な質問に対する回答を生成するサービス"""

    SYSTEM_PROMPT = """## あなたの役割:
あなたはBRANU株式会社の社内アシスタントAIとして、社員からの質問や依頼に回答します。
親切で正確な対応を心がけてください。

## 回答のスタイル:

- **自然な会話**: 堅苦しくならず、親しみやすい言葉遣いで回答してください
- **簡潔さ**: 質問に直接答え、必要な情報を過不足なく提供してください
- **わかりやすさ**: 専門用語を使う場合は簡単に説明を加えてください

## Slack mrkdwn形式:
- 太字: `*テキスト*` の形式で囲む
- 箇条書き: 各行の先頭に `• ` を使用
- 見出し記号(`#`, `##`, `###`)は使用しない

## 制約:
- 学習済み知識(2025年1月まで)の範囲内で回答してください
- 最新情報が必要な場合や不確実な情報は推測せず、素直にその旨を伝えてください
- 「BRANU株式会社の社内アシスタントAIです」のような自己紹介は回答に含めないでください"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(self, chat_session: ChatSession, task: Task):
        """タスクを実行して回答を生成し、タスクを完了させる

        Args:
            chat_session: チャットセッション(会話履歴を含む)
            task: 実行するタスク

        Returns:
            完了済みのタスク
        """
        # タスク用のプロンプトを構築(日付情報を含む)
        task_prompt = self._build_task_prompt(task.description)

        # メッセージリストを構築
        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            *chat_session.messages,
            Message.create_user_message(task_prompt),
        ]

        # LLMで回答生成
        answer = await self.llm_client.generate(messages)

        # タスクを完了させる
        task.complete(answer)

    def _get_current_date(self) -> str:
        """現在の日付を取得する"""
        return datetime.now().strftime("%Y年%m月%d日")

    def _build_task_prompt(self, task_description: str) -> str:
        """タスクプロンプトを構築する"""
        current_date = self._get_current_date()

        return f"""## 現在の日付:
{current_date}

## タスク:
{task_description}

上記のタスクについて回答してください。"""
