from datetime import datetime
from uuid import uuid4

import pytest

from src.domain.exception.chat_session_exception import (
    AssistantMessageNotFoundError,
    InvalidAssistantMessageRoleError,
    InvalidUserMessageRoleError,
    NoneTaskPlanError,
    UserMessageNotFoundError,
)
from src.domain.model.chat_session import ChatSession
from src.domain.model.message import Message, Role
from src.domain.model.task import Task
from src.domain.model.task_plan import TaskPlan


def test_create_chat_session():
    """チャットセッションを生成するテスト"""
    session_id = "test-session-1"
    thread_id = "thread-123"
    user_id = "U12345"
    channel_id = "C12345"

    session = ChatSession.create(
        id=session_id, thread_id=thread_id, user_id=user_id, channel_id=channel_id
    )

    assert session.id == session_id
    assert session.thread_id == thread_id
    assert session.user_id == user_id
    assert session.channel_id == channel_id
    assert session.messages == []
    assert session.task_plans == []
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
    assert session.created_at == session.updated_at


def test_create_chat_session_without_thread():
    """スレッドなしでチャットセッションを生成するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    assert session.thread_id is None


def test_reconstruct_chat_session():
    """チャットセッションを再構築するテスト"""
    session_id = "session-1"
    thread_id = "thread-123"
    user_id = "U12345"
    channel_id = "C12345"
    messages = [Message.create_user_message("こんにちは")]
    task_plans = []
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    updated_at = datetime(2024, 1, 2, 12, 0, 0)

    session = ChatSession.reconstruct(
        id=session_id,
        thread_id=thread_id,
        user_id=user_id,
        channel_id=channel_id,
        messages=messages,
        task_plans=task_plans,
        created_at=created_at,
        updated_at=updated_at,
    )

    assert session.id == session_id
    assert session.thread_id == thread_id
    assert session.user_id == user_id
    assert session.channel_id == channel_id
    assert session.messages == messages
    assert session.task_plans == task_plans
    assert session.created_at == created_at
    assert session.updated_at == updated_at


def test_add_user_message_with_string():
    """文字列でユーザーメッセージを追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    content = "こんにちは"

    session.add_user_message(content)

    assert len(session.messages) == 1
    assert session.messages[0].role == Role.USER
    assert session.messages[0].content == content


def test_add_user_message_with_message_object():
    """Messageオブジェクトでユーザーメッセージを追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    message = Message.create_user_message("こんにちは")

    session.add_user_message(message)

    assert len(session.messages) == 1
    assert session.messages[0] == message


def test_add_user_message_with_wrong_role_raises_error():
    """間違ったロールのメッセージを追加するとエラーになるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    assistant_message = Message.create_assistant_message("こんにちは")

    with pytest.raises(
        InvalidUserMessageRoleError, match="USER以外のメッセージは追加できません"
    ):
        session.add_user_message(assistant_message)


def test_add_assistant_message_with_string():
    """文字列でアシスタントメッセージを追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    content = "こんにちは！何かお手伝いできますか?"

    session.add_assistant_message(content)

    assert len(session.messages) == 1
    assert session.messages[0].role == Role.ASSISTANT
    assert session.messages[0].content == content


def test_add_assistant_message_with_message_object():
    """Messageオブジェクトでアシスタントメッセージを追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    message = Message.create_assistant_message("こんにちは！")

    session.add_assistant_message(message)

    assert len(session.messages) == 1
    assert session.messages[0] == message


def test_add_assistant_message_with_wrong_role_raises_error():
    """間違ったロールのメッセージを追加するとエラーになるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    user_message = Message.create_user_message("こんにちは")

    with pytest.raises(
        InvalidAssistantMessageRoleError,
        match="ASSISTANT以外のメッセージは追加できません",
    ):
        session.add_assistant_message(user_message)


def test_add_multiple_messages():
    """複数のメッセージを追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    session.add_user_message("質問1")
    session.add_assistant_message("回答1")
    session.add_user_message("質問2")
    session.add_assistant_message("回答2")

    assert len(session.messages) == 4
    assert session.messages[0].role == Role.USER
    assert session.messages[1].role == Role.ASSISTANT
    assert session.messages[2].role == Role.USER
    assert session.messages[3].role == Role.ASSISTANT


def test_last_user_message():
    """直近のユーザーメッセージを取得するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    session.add_user_message("質問1")
    session.add_assistant_message("回答1")
    session.add_user_message("質問2")
    session.add_assistant_message("回答2")

    last_message = session.last_user_message()

    assert last_message.content == "質問2"
    assert last_message.role == Role.USER


def test_last_user_message_when_no_user_messages():
    """ユーザーメッセージがない場合は例外を投げるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    session.add_assistant_message("回答のみ")

    with pytest.raises(
        UserMessageNotFoundError, match="ユーザーメッセージが存在しません"
    ):
        session.last_user_message()


def test_last_user_message_when_empty():
    """メッセージが空の場合は例外を投げるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    with pytest.raises(
        UserMessageNotFoundError, match="ユーザーメッセージが存在しません"
    ):
        session.last_user_message()


def test_last_assistant_message_id():
    """直近のアシスタントメッセージIDを取得するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    session.add_user_message("質問1")
    session.add_assistant_message("回答1")
    session.add_user_message("質問2")
    assistant_message = Message.create_assistant_message("回答2")
    session.add_assistant_message(assistant_message)

    last_id = session.last_assistant_message_id()

    assert last_id == str(assistant_message.id)


def test_last_assistant_message_id_when_no_assistant_messages():
    """アシスタントメッセージがない場合は例外を投げるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    session.add_user_message("質問のみ")

    with pytest.raises(
        AssistantMessageNotFoundError, match="アシスタントメッセージが存在しません"
    ):
        session.last_assistant_message_id()


def test_last_assistant_message_id_when_empty():
    """メッセージが空の場合は例外を投げるテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    with pytest.raises(
        AssistantMessageNotFoundError, match="アシスタントメッセージが存在しません"
    ):
        session.last_assistant_message_id()


def test_add_task_plan():
    """タスク計画を追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )
    message_id = uuid4()
    tasks = [Task.create_web_search("検索タスク")]
    task_plan = TaskPlan.create(message_id=message_id, tasks=tasks)

    session.add_task_plan(task_plan)

    assert len(session.task_plans) == 1
    assert session.task_plans[0] == task_plan


def test_add_multiple_task_plans():
    """複数のタスク計画を追加するテスト"""
    session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    task_plan1 = TaskPlan.create(
        message_id=uuid4(), tasks=[Task.create_web_search("検索1")]
    )
    task_plan2 = TaskPlan.create(
        message_id=uuid4(), tasks=[Task.create_general_answer("回答1")]
    )

    session.add_task_plan(task_plan1)
    session.add_task_plan(task_plan2)

    assert len(session.task_plans) == 2
    assert session.task_plans[0] == task_plan1
    assert session.task_plans[1] == task_plan2
