from typing import Literal

from pydantic import BaseModel, Field

from ..llm_client import LLMClient
from ..model import ChatSession, Message, Task, TaskPlan


class TaskPlanningService:
    SYSTEM_PROMPT = """ユーザーのリクエストを実行可能な独立したサブタスクに分割してください。

# システムアーキテクチャ:
1. **タスク計画（あなたの役割）**: リクエストを複数のタスクに分割し、適切なエージェントに割り当てる
2. **タスク実行**: 各エージェントが並列実行し、結果を返す
3. **回答生成**: すべての結果を統合して最終回答を生成

**重要**: 各タスクは並列実行されます

# 利用可能なエージェント

- **general_answer**: 一般回答エージェント
    - 一般的な質問に回答
    - 内部知識ベースや事前学習済みモデルを使用

- **web_search**: Web検索エージェント
    - Google検索を実行し、ページ内容を取得・分析
    - 最新ニュース、天気、技術情報など、Web上の公開情報の取得に最適

# サブタスク作成ルール

1. **必ず1つ以上のサブタスクを作成**
2. **各タスクは完全に独立** - 依存関係を持たせない
3. **タスク内容は具体的で明確に** - エージェントへの指示として機能するように記述
"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def execute(self, chat_session: ChatSession) -> TaskPlan:
        class _Task(BaseModel):
            task_description: str = Field(description="タスクの内容を簡潔に記述してください。")
            next_agent: Literal["general_answer", "web_search"] = Field(description="処理するエージェント")

        class _TaskPlan(BaseModel):
            tasks: list[_Task] = Field(description="実行するタスクのリスト（最低1つ以上）")
            reason: str = Field(description="タスク分割の戦略と根拠を説明してください。")

        messages = [
            Message.create_system_message(self.SYSTEM_PROMPT),
            *chat_session.messages
        ]

        task_plan = await self.llm_client.generate_with_structured_output(messages, _TaskPlan)

        tasks = []
        for task_info in task_plan.tasks:
            if task_info.next_agent == "web_search":
                task = Task.create_web_search(task_info.task_description)
            elif task_info.next_agent == "general_answer":
                task = Task.create_general_answer(task_info.task_description)
            else:
                raise ValueError(f"不明なエージェントです: {task_info.next_agent}")

            tasks.append(task)

        latest_message = chat_session.last_user_message()
        if not latest_message:
            raise ValueError("ユーザーメッセージが見つかりません")

        task_plan = TaskPlan.create(
            message_id=latest_message.id,
            tasks=tasks
        )

        return task_plan










