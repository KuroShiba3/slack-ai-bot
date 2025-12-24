from typing import Annotated, TypedDict

from ....domain.model import ChatSession, TaskPlan


def take_first(left, right):
    """複数の値が来た場合、最初の値を採用する

    mutableなドメインオブジェクト(ChatSession, TaskPlan)は参照渡しなので
    複数のノードから返されても実際には同じオブジェクト。
    最初の値を取ることで、変更された同じオブジェクトを保持する。
    """
    return left if left is not None else right


class Context(TypedDict):
    channel_id: str
    thread_ts: str
    message_ts: str
    user_id: str


class BaseState(TypedDict):
    chat_session: Annotated[ChatSession, take_first]
    context: Context
    task_plan: Annotated[TaskPlan | None, take_first]
    answer: str | None
