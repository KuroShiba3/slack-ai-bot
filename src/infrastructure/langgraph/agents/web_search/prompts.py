from datetime import datetime


def get_search_query_system(current_date: str = None) -> str:
    if current_date is None:
        current_date = datetime.now().strftime("%Y年%m月%d日")

    return f"""あなたは検索クエリ生成の専門家です。割り当てられたタスクに答えるために最適な検索クエリを生成してください。

## 現在の日付:
{current_date}

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


def get_search_query_human(task_description: str, previous_queries: list[str] = None, feedback: str = None) -> str:
    parts = [f"## 割り当てられたタスク:\n{task_description}"]

    if previous_queries:
        queries_text = "\n".join([f"- {q}" for q in previous_queries])
        parts.append(f"\n## すでに利用した検索クエリ:\n{queries_text}")
        parts.append("\n**重要**: 前回の検索で十分な結果が得られなかったため、異なる角度からの新しいクエリを生成してください。")

    if feedback:
        parts.append(f"\n## 改善フィードバック:\n{feedback}")
        parts.append("\n上記のフィードバックを参考にしてください。")

    return "".join(parts)


def get_task_result_system(current_date: str = None) -> str:
    if current_date is None:
        current_date = datetime.now().strftime("%Y年%m月%d日")

    return f"""あなたはタスク実行エージェントです。以下の検索結果を元に、割り当てられたタスクの結果をまとめてください。

## 現在の日付:
{current_date}

## システムアーキテクチャの理解:
1. **タスク計画**: ユーザーの質問を複数のタスクに分割
2. **タスク実行（あなたの役割）**: 各タスクについて検索を実行し、結果をまとめる
3. **回答生成**: すべてのタスク結果を統合してユーザーに最終回答を提示

**重要**: 回答生成エージェントは検索結果を直接見ることができません。

## タスク結果作成のルール:

1. **検索結果のみを使用**:
    - 検索結果に含まれる情報のみを使用
    - 推測しない

2. **次のエージェントが理解できる内容**:
    - 数字、日付、固有名詞など具体的な情報を含める
    - 専門用語は簡潔に補足

3. **情報源の記載（必須）**:
    - 引用番号: [0], [1] のように角括弧で囲む
    - Slackリンク形式: `<URL|表示名>`
    - **URLは一字一句完全にコピー（変更・創作厳禁）**

4. **フォーマット**:
    ```
    （タスク結果の本文）[0][1]

    【参考情報】（2件）
    [0] <URL|表示名>
    [1] <URL|表示名>
    ```"""


def get_task_result_human(task_description: str, search_results: list[dict], feedback: str = None, previous_result: str = None) -> str:
    parts = [f"## 割り当てられたタスク:\n{task_description}"]

    if search_results:
        parts.append("\n## 取得した検索結果:")
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", result.get("snippet", ""))
            query = result.get("query", "")

            parts.append(f"\n### 検索結果 {i}")
            parts.append(f"\n**検索クエリ**: {query}")
            parts.append(f"\n**タイトル**: {title}")
            parts.append(f"\n**URL**: {url}")
            parts.append(f"\n**内容**:\n{content}\n")
        parts.append("\n**【重要】URLを【参考情報】に含める場合は、一字一句完全にコピーしてください。**")

    if feedback:
        parts.append(f"\n## 改善フィードバック:\n{feedback}")
        if previous_result:
            parts.append(f"\n## 以前のタスク結果:\n{previous_result}")
        parts.append("\n**重要**: フィードバックを参考にして、より良いタスク結果を作成してください。")

    return "".join(parts)


def get_evaluate_task_result_system(current_date: str = None) -> str:
    if current_date is None:
        current_date = datetime.now().strftime("%Y年%m月%d日")

    return f"""あなたはタスク結果品質を評価する専門家です。

## 現在の日付:
{current_date}

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


def get_evaluate_task_result_human(task_description: str, task_result: str, search_results: list = None) -> str:
    """評価用のヒューマンメッセージを生成"""
    parts = [
        f"## 割り当てられたタスク:\n{task_description}",
        f"\n## 生成されたタスク結果:\n{task_result}"
    ]

    if search_results:
        parts.append("\n## 取得した検索結果:")
        for i, result in enumerate(search_results, 1):
            parts.append(f"\n### 検索結果 {i}")
            parts.append(f"\n**URL**: {result.url}")
            parts.append(f"\n**タイトル**: {result.title}")

    return "".join(parts)