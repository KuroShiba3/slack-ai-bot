from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import AnyMessage, add_messages

class SlackContext(TypedDict):
    channel_id: str
    thread_ts: str
    message_ts: str
    user_id: str

class Task(TypedDict):
    task_id: str
    task_description: str
    task_result: str

def update_task(existing: list[Task], new: list[Task]) -> list[Task]:
    """タスクリストを更新（新しいタスクで既存のタスクを置き換える）"""
    if not new:
        return existing

    # 新しいタスクのIDセットを作成
    new_task_ids = {task['task_id'] for task in new}

    # 既存タスクのうち、更新されないものを保持
    updated = [task for task in existing if task['task_id'] not in new_task_ids]

    # 新しいタスクを追加
    updated.extend(new)

    return updated

class BaseState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    slack_context: SlackContext
    tasks: Annotated[list[Task], update_task]
    final_answer: Optional[str]
    user_message_id: Optional[str]
    ai_message_id: Optional[str]