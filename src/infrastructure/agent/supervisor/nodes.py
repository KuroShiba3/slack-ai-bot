from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import END
from langgraph.types import Command, Send
from pydantic import BaseModel, Field

from ...config.model import get_embedding_model, get_model
from ...db.client import DatabaseClient
from ...db.models import ConversationSession, Message, Task
from ...slack.actions import add_slack_reaction
from ...state.state import BaseState
from ...utils.error import send_error_to_slack
from ...utils.logger import get_logger
from .utils import normalize_ai_messages

logger = get_logger(__name__)

async def decide_response_method(state: BaseState) -> Command:
    """ユーザーのリクエストを分析し、直接回答するか専門エージェントに依頼するかを決定するノード"""

    # Slackコンテキストからセッション情報を取得
    slack_context = state.get("slack_context", {})
    channel_id = slack_context.get("channel_id")
    thread_ts = slack_context.get("thread_ts")
    message_ts = slack_context.get("message_ts")
    session_ts = thread_ts or message_ts
    user_id = slack_context.get("user_id")

    user_message_id = None
    if channel_id and session_ts:
        try:
            db_client = DatabaseClient()

            session_id = f"{channel_id}_{session_ts}"

            session = ConversationSession(id=session_id)
            await db_client.create_session(session)

            # ユーザーメッセージを保存
            messages = state.get("messages", [])
            if messages and hasattr(messages[-1], 'type') and messages[-1].type == "human":
                # メッセージ内容
                message_content = messages[-1].content

                # エンベディング生成(humanメッセージの場合のみ)
                embedding = None
                try:
                    embedding_model = get_embedding_model()
                    embeddings = await embedding_model.aembed_documents([message_content])
                    if embeddings and len(embeddings) > 0:
                        embedding = embeddings[0]
                except Exception as e:
                    logger.error(f"エンベディング生成に失敗しました: {e}")

                user_message = Message(
                    session_id=session_id,
                    user_id=user_id,
                    message_type="human",
                    content=message_content,
                    embedding=embedding
                )
                saved_message = await db_client.save_message(user_message)
                if saved_message:
                    user_message_id = str(saved_message.id)

        except Exception as e:
            logger.error(f"データベースへの保存に失敗しました: {e}")

    class ResponseDecision(BaseModel):
        can_answer_directly: bool = Field(description="学習済み知識だけで回答できるかどうか。検索や外部情報が不要な場合はTrue")
        reason: str = Field(description="判断理由を具体的に記述")

    system_message = SystemMessage(
        content="""
## あなたの役割:
あなたはBRANU株式会社の社内アシスタントAIです。
社員からの質問や依頼に対して、親切で正確な対応を心がけてください。

## タスク:
ユーザーのリクエストを分析し、学習済み知識だけで回答できるか判断してください。

## システムアーキテクチャの理解:
このシステムは以下の段階で動作します:
1. **処理方法の判断(あなたの役割)**: ユーザーのリクエストを分析し、直接回答するか、専門エージェントに依頼するかを決定
2. **タスク計画**: 専門エージェントが必要な場合、リクエストを複数のタスクに分割し、各タスクを適切なエージェントに割り当てる
3. **タスク実行**: 各エージェント(general、regulation)が割り当てられたタスクを並列実行し、検索や情報収集を行って結果を返す
4. **回答生成**: すべてのタスク結果を統合してユーザーに最終回答を提示

**あなたの役割**:
- 学習済み知識だけで答えられる質問 → 直接回答(ステップ2-4をスキップ)
- 検索や外部情報が必要な質問 → 専門エージェントに依頼(ステップ2-4を実行)

## 判断基準

### 直接回答できる場合 (`can_answer_directly: true`)

以下の場合は学習済み知識だけで回答できます:

- **一般的な知識**: プログラミングの基礎、歴史、科学、数学など
- **簡単な計算や変換**: 単位変換、簡単な計算、日付計算など
- **挨拶や雑談**: こんにちは、ありがとう、自己紹介など
- **概念の説明**: 用語の定義、仕組みの説明など
- **2025年1月以前の情報**: 最新情報が不要な質問

### 専門エージェントが必要な場合 (`can_answer_directly: false`)

以下の場合は専門エージェント(websearch、regulation)に依頼が必要です:

- **Web検索が必要**: 今日の天気、最新ニュース、株価、現在の状況、特定のサイト情報、具体的な製品情報など
- **社内規定が必要**: 就業規則、有給休暇、経費ルール、ガイドラインなど

## 重要な注意事項
- 会話履歴全体を参照してユーザーの意図を理解してください
- 少しでも外部情報が必要な場合は、専門エージェントに依頼してください
"""
    )

    normalized_messages = normalize_ai_messages(state["messages"])
    messages = [system_message, *normalized_messages]

    try:
        model = get_model()
        decision = await model.with_structured_output(ResponseDecision).ainvoke(messages)

        if decision.can_answer_directly:
            latest_question = normalized_messages[-1].content if normalized_messages else ""
            logger.info(
                "利用機能ログ",
                extra={
                    "type": "direct_answer",
                    "query": latest_question,
                }
            )
            return Command(
                update={"user_message_id": user_message_id},
                goto="generate_direct_answer"
            )

        return Command(
            update={"user_message_id": user_message_id},
            goto="plan_tasks"
        )

    except Exception as e:
        logger.error(f"decide_response_methodでエラーが発生しました: {e!s}", exc_info=True)
        raise


async def generate_direct_answer(state: BaseState) -> Command:
    """学習済み知識で直接回答を生成するノード"""

    normalized_messages = normalize_ai_messages(state["messages"])

    system_message = SystemMessage(
        content=f"""
## あなたの役割:
あなたはBRANU株式会社の社内アシスタントAIとして、社員からの質問や依頼に回答します。
親切で正確な対応を心がけてください。

## 現在の日付:
{datetime.now().strftime("%Y年%m月%d日")}

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
- 「BRANU株式会社の社内アシスタントAIです」のような自己紹介は回答に含めないでください
"""
    )

    messages = [system_message, *normalized_messages]

    try:
        model = get_model()
        response = await model.ainvoke(messages)

        slack_context = state.get("slack_context", {})
        channel_id = slack_context.get("channel_id")
        thread_ts = slack_context.get("thread_ts")
        message_ts = slack_context.get("message_ts")
        session_ts = thread_ts or message_ts

        ai_message_id = None
        if channel_id and session_ts:
            try:
                db_client = DatabaseClient()
                session_id = f"{channel_id}_{session_ts}"

                ai_message = Message(
                    session_id=session_id,
                    user_id=None,
                    message_type="ai",
                    content=response.content
                )
                saved_ai_message = await db_client.save_message(ai_message)
                ai_message_id = str(saved_ai_message.id) if saved_ai_message else None
            except Exception as e:
                logger.error(f"AIメッセージの保存に失敗しました: {e}")

        return Command(
            update={
                "messages": [AIMessage(content=response.content)],
                "final_answer": response.content,
                "ai_message_id": ai_message_id
            },
            goto=END
        )

    except Exception as e:
        logger.error(f"generate_direct_answerでエラーが発生しました: {e!s}", exc_info=True)
        raise


async def plan_tasks(state: BaseState) -> Command:
    """ユーザーのリクエストを分析し、実行可能な独立したサブタスクに分割するノード"""

    slack_context = state.get("slack_context", {})
    if slack_context:
        channel = slack_context.get("channel_id")
        message_ts = slack_context.get("message_ts")
        await add_slack_reaction(channel, message_ts, "eyes")

    class _Task(BaseModel):
        task_description: str = Field(description="タスクの内容を簡潔に記述してください。")
        next_agent: Literal["websearch", "regulation"] = Field(description="処理するエージェント")

    class TaskPlan(BaseModel):
        tasks: list[_Task] = Field(description="実行するタスクのリスト(最低1つ以上)")
        reason: str = Field(description="タスク分割の戦略と根拠を説明してください。")

    system_message = SystemMessage(
        content="""
ユーザーのリクエストを実行可能な独立したサブタスクに分割してください。

## システムアーキテクチャの理解:
このシステムは以下の3段階で動作します:
1. **タスク計画(あなたの役割)**: ユーザーのリクエストを複数のタスクに分割し、各タスクを適切なエージェントに割り当てる
2. **タスク実行**: 各エージェントが割り当てられたタスクを並列実行し、検索や情報収集を行って結果を返す
3. **回答生成**: すべてのタスク結果を統合してユーザーに最終回答を提示

**重要**:
- 各タスクは対応するエージェントが独立して実行します
- 複数のタスクは並列実行されます
- あなたが作成したタスクの内容が、各エージェントへの指示になります

## 利用可能なエージェント

- **websearch**: Web検索エージェント
    - Google検索を実行し、検索結果のページ内容を取得・分析
    - 最大2個の検索クエリを生成し、各クエリで最大2件のページを取得
    - ページの本文コンテンツを読み込み、タスクに関連する情報を抽出
    - 検索結果の評価を行い、必要に応じて検索クエリを改善して再検索
    - 最新ニュース、天気、技術情報、製品情報など、Web上の公開情報の取得に最適

- **regulation**: 社内規定検索エージェント
    - Vertex AI Search (Grounding機能付き) で社内規定を検索
    - 就業規則、有給休暇、経費ルール、各種ガイドラインなど社内文書を検索
    - 最大2個の検索クエリを生成し、複数の角度から規定を検索
    - 検索結果には出典情報(規定ファイル名、該当箇所のスニペット)が自動的に付与される
    - 複数の検索結果を統合し、矛盾がある場合は両方の情報を提示
    - 検索結果の評価を行い、必要に応じて検索クエリを改善して再検索
    - 社内規定、会社のポリシー、内部ルールに関する質問に最適

## エージェント選択の重要なルール
**社内規定に関する質問の場合は、必ずregulationエージェントのみを使用してください。**
- 社内規定の情報はregulationエージェントの専用データストアにのみ存在します

## サブタスクの作成ルール

### 基本方針
- **並列実行を活用**: 複数のエージェントが同時に実行できるため、独立したタスクは分割してください
- **検索の効率化**: 異なる対象(場所、期間、項目など)は別々のタスクにすることで、検索精度が向上します

### 必須要件

1. **必ず1つ以上のサブタスクを作成してください**
    - 単一の質問でも、最低1つのサブタスクを作成します

2. **各サブタスクは完全に独立している必要があります**
    - タスク間に依存関係を持たせないでください
    - あるタスクの結果が別のタスクの入力になるような分割は避けてください
    - 各タスクは単独で実行・完了できる内容にしてください
    - 各タスクは並列実行されるため、順序に依存しない設計にしてください

3. **タスクの内容は具体的で明確にしてください**
    - エージェントへの指示として機能するよう、タスクの内容を明確に記述してください
    - 「〇〇について調べる」のように、エージェントが何をすべきか分かるように記述してください

## 重要な注意事項
- 会話履歴全体を参照してユーザーの意図を理解してください
- 各サブタスクの内容は明確で具体的にしてください
- 適切なエージェントを選択してください
"""    )

    normalized_messages = normalize_ai_messages(state["messages"])
    messages = [system_message, *normalized_messages]

    try:
        model = get_model("gemini-2.5-flash")
        plan = await model.with_structured_output(TaskPlan).ainvoke(
            messages
        )

        if not plan.tasks:
            # 念のため(通常は来ないはず)
            logger.error("plan_tasksでtasksが空です")
            await send_error_to_slack(state, "エラーが発生しました。新しいスレッドで再度お試しください。")
            return Command(goto=END)

        # 利用機能をログ出力
        agent_types = [task.next_agent for task in plan.tasks]
        primary_agent = "regulation" if "regulation" in agent_types else "websearch"
        latest_question = normalized_messages[-1].content if normalized_messages else ""

        logger.info(
            "利用機能ログ",
            extra={
                "type": primary_agent,
                "query": latest_question,
            }
        )

        user_message_id = state.get("user_message_id")
        saved_task_ids = []

        if user_message_id:
            try:
                db_client = DatabaseClient()

                for task in plan.tasks:
                    # 各タスクにUUIDを生成
                    task_uuid = uuid4()
                    db_task = Task(
                        id=task_uuid,
                        message_id=UUID(user_message_id),
                        task_description=task.task_description,
                        agent_type=task.next_agent,
                        result=None
                    )
                    saved_task = await db_client.save_task(db_task)
                    if saved_task:
                        saved_task_ids.append(str(saved_task.id))
                    else:
                        saved_task_ids.append(str(task_uuid))
            except Exception as e:
                logger.error(f"タスクの保存に失敗しました: {e}")
                saved_task_ids = [str(uuid4()) for _ in plan.tasks]
        else:
            saved_task_ids = [str(uuid4()) for _ in plan.tasks]

        sends = [
            Send(
                task.next_agent,
                {
                    "task_id": saved_task_ids[idx],
                    "task_description": task.task_description,
                    "attempt": 0,
                    "completed": False
                }
            )
            for idx, task in enumerate(plan.tasks)
        ]

        initial_tasks = [
            {
                "task_id": saved_task_ids[idx],
                "task_description": task.task_description,
                "task_result": ""
            }
            for idx, task in enumerate(plan.tasks)
        ]

        return Command(
            update={"tasks": initial_tasks},
            goto=sends
        )
    except Exception as e:
        logger.error(f"plan_tasksでエラーが発生しました: {e!s}", exc_info=True)
        raise

async def generate_final_answer(state: BaseState) -> Command:
    """完了したタスクの結果を統合して、ユーザーへの最終回答を生成"""

    tasks = state.get("tasks", [])

    if not tasks:
        error_msg = "タスクが存在しません"
        logger.error(f"generate_final_answer: {error_msg}")
        raise ValueError(error_msg)

    # タスク結果を整形
    task_results_text = "\n\n".join([
        f"【タスク{idx+1}】{task['task_description']}\n結果: {task['task_result']}"
        for idx, task in enumerate(tasks)
    ])

    # 会話履歴を正規化
    messages = state.get("messages", [])
    normalized_messages = normalize_ai_messages(messages)

    # 最新の質問を取得
    latest_question = messages[-1].content

    system_message = SystemMessage(content=f"""
## あなたの役割:
あなたはBRANU株式会社の社内アシスタントAIとして、社員からの質問や依頼に回答します。
親切で正確な対応を心がけてください。

## タスク:
複数のタスクの実行結果を統合し、ユーザーの質問に対する包括的で分かりやすい回答を生成してください。

## 現在の日付:
{datetime.now().strftime("%Y年%m月%d日")}

## 回答のルール:

1. **統合と一貫性**:
    - 各タスクの結果を適切に統合し、全体として一貫性のある回答にする
    - タスクの結果を単純に羅列するのではなく、自然な文章として統合する
    - 矛盾がある場合は両方の情報を提示し、違いを明確にする

2. **簡潔さと適切な情報量のバランス**:
    - ユーザーの質問に直接答える形式にする
    - 質問の範囲内で重要な情報を過不足なく提供する
    - 関連する重要な注意事項や制限事項は簡潔に含める
    - ただし、質問されていない詳細な手続きや補足情報は省略する
    - 見出しは最小限にし、1レベルまでに抑える(サブセクション「###」は使用しない)

3. **わかりやすさ**:
    - 簡潔で分かりやすい日本語で記述
    - 重要度の高い情報を優先的に記載する
    - 箇条書きは3〜5項目程度に抑え、サブ項目は必要最小限にする

4. **完全性よりも関連性を重視**:
    - タスク結果の全ての情報を含めるのではなく、質問に関連する重要な情報のみを選択する
    - 矛盾がある場合は両方の情報を提示し、違いを明確にする

5. **Slack mrkdwn形式(厳守)**:
    - Slackのmrkdwn形式を使用(標準Markdownとは異なる)
    - 太字: `*テキスト*` の形式で囲む
    - 箇条書き: 各行の先頭に `• ` を使用
    - ネストした箇条書きは2階層まで使用可能(1階層目: `• `、2階層目: `    • `でインデント)
    - 見出し記号(`#`, `##`, `###`)は使用しない
    - 水平線(`---`)は使用しない
    - セクション分けは空行と太字テキストで表現する

6. **情報源の記載形式(必須)**:
    - **【最重要】URLやファイル名の創作・推測・ハルシネーションは絶対禁止**
    - **タスク結果に存在しないURLやファイル名を絶対に記載しないでください**
    - **タスク結果に含まれるURLをそのまま正確にコピーして使用すること**
    - **URLやファイル名を少しでも変更・修正・推測することは厳禁**
    - **タスク結果に含まれる出典形式(インライン引用番号と【参考情報】セクション)をそのまま維持してください**
    - 引用番号の形式: [0], [1] のように角括弧で囲む
    - 各タスク結果の出典情報を統合する場合、番号を振り直して一貫性を保つ
    - **同じファイル名・URLが複数ある場合は1つにまとめる**:
        - 例: [0] file.pdf, [1] file.pdf, [2] file.pdf → [0] file.pdf として統合
        - 本文中の引用番号も統合後の番号に合わせて調整
    - **重要: テキストスニペットは【参考情報】セクションにのみ記載し、本文中には含めないでください**
    - **テキストスニペット(`> 該当箇所のテキスト...`)がタスク結果に含まれている場合は、【参考情報】セクションに保持してください**
    - タスク結果で実際に利用した情報源のみを記載する
    - URLの最大個数制限はなし(すべての重要な情報源を記載)
    - **Slack形式のマークダウンリンクを使用**: `<URL|表示名>` の形式で記述
    - フォーマット例(スニペットあり):
    ```
    (最終的な回答の本文。スニペットは含めない)[0][1]

    【参考情報】(2件)
    [0] <URL|表示名>
    > 該当箇所のテキストスニペット…(詳細はリンク先)
    [1] <URL|表示名>
    > 該当箇所のテキストスニペット…(詳細はリンク先)
    ```
    - フォーマット例(スニペットなし):
    ```
    (最終的な回答の本文)[0][1]

    【参考情報】(2件)
    [0] <URL|表示名>
    [1] <URL|表示名>
    ```

## 重要な注意事項:
- タスク結果に含まれる情報を中心に回答を構成してください
- 情報が不足している場合は、その旨を明記してください
- **【絶対厳守】URLやファイル名のハルシネーション(創作・推測・捏造)は絶対禁止**
- **タスク結果に含まれるURLとファイル名を一字一句完全にコピーして使用すること**
- **URLの文字列(特にファイルID)は一文字も変更・編集・間違えてはいけません**
- **存在しないURLやファイル名を作成したり、推測したりすることは絶対に禁止**
- **URLを記憶から再生成することは厳禁(必ずタスク結果からコピー)**
- 情報源URLは必ず記載してください(タスク結果にURLが含まれている場合)
- 「BRANU株式会社の社内アシスタントAIです」のような自己紹介は回答に含めないでください

## 社内規定に関する質問の場合の厳格ルール(regulation タスクがある場合):
- **タスク結果に含まれる情報のみを使用すること(最重要)**
- **タスク結果にない情報は絶対に推測・創作・補完しないこと**
- **学習済み知識や一般常識で社内規定を補足することは絶対に禁止**
- **推測・推定・類推による回答は厳禁**
- タスク結果が不十分な場合は、「該当する記載が見つかりませんでした」と明記すること
""")

    human_message = HumanMessage(content=f"""
## ユーザーの質問:
{latest_question}

## タスクの実行結果:
{task_results_text}

上記のタスク結果を統合して、ユーザーの質問に対する包括的な回答を生成してください。

**【重要】タスク結果に含まれる【参考情報】セクションのURLは、一字一句完全にコピーしてください。URLの文字を変更・間違えることは絶対禁止です。**
""")

    try:
        model = get_model("gemini-2.5-flash")
        response = await model.ainvoke([system_message, *normalized_messages[:-1], human_message])

        slack_context = state.get("slack_context", {})
        channel_id = slack_context.get("channel_id")
        thread_ts = slack_context.get("thread_ts")
        message_ts = slack_context.get("message_ts")
        session_ts = thread_ts or message_ts

        ai_message_id = None
        if channel_id and session_ts:
            try:
                db_client = DatabaseClient()
                session_id = f"{channel_id}_{session_ts}"

                ai_message = Message(
                    session_id=session_id,
                    user_id=None,
                    message_type="ai",
                    content=response.content
                )
                saved_ai_message = await db_client.save_message(ai_message)
                ai_message_id = str(saved_ai_message.id) if saved_ai_message else None
            except Exception as e:
                logger.error(f"AIメッセージの保存に失敗しました: {e}")

        return Command(
            update={
                "messages": [AIMessage(content=response.content)],
                "final_answer": response.content,
                "ai_message_id": ai_message_id
            },
            goto=END
        )

    except Exception as e:
        logger.error(f"generate_final_answerでエラーが発生しました: {e!s}", exc_info=True)
        raise
