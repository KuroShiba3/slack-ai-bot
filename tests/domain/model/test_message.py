from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.domain.exception.message_exception import EmptyMessageContentError
from src.domain.model.message import Message, Role


def test_create_user_message():
    """ユーザーメッセージの生成テスト"""
    content = "こんにちは"
    message = Message.create_user_message(content)

    assert message.role == Role.USER
    assert message.content == content
    assert isinstance(message.id, UUID)
    assert isinstance(message.created_at, datetime)


def test_create_assistant_message():
    """アシスタントメッセージの生成テスト"""
    content = "こんにちは、何かお手伝いできることはありますか?"
    message = Message.create_assistant_message(content)

    assert message.role == Role.ASSISTANT
    assert message.content == content
    assert isinstance(message.id, UUID)
    assert isinstance(message.created_at, datetime)


def test_create_system_message():
    """システムメッセージの生成テスト"""
    content = "あなたは親切なアシスタントです"
    message = Message.create_system_message(content)

    assert message.role == Role.SYSTEM
    assert message.content == content
    assert isinstance(message.id, UUID)
    assert isinstance(message.created_at, datetime)


def test_create_with_role():
    """ロールを指定したメッセージ生成テスト"""
    content = "テストメッセージ"
    message = Message.create(Role.USER, content)

    assert message.role == Role.USER
    assert message.content == content
    assert isinstance(message.id, UUID)
    assert isinstance(message.created_at, datetime)


def test_reconstruct():
    """既存データからのメッセージ再構築テスト"""
    message_id = uuid4()
    role = Role.ASSISTANT
    content = "再構築されたメッセージ"
    created_at = datetime.now()

    message = Message.reconstruct(
        id=message_id, role=role, content=content, created_at=created_at
    )

    assert message.id == message_id
    assert message.role == role
    assert message.content == content
    assert message.created_at == created_at


def test_empty_content_raises_error():
    """空のコンテンツでエラーが発生することをテスト"""
    with pytest.raises(EmptyMessageContentError, match="メッセージの内容が空です"):
        Message.create_user_message("")


def test_whitespace_only_content_raises_error():
    """空白文字のみのコンテンツでエラーが発生することをテスト"""
    with pytest.raises(EmptyMessageContentError, match="メッセージの内容が空です"):
        Message.create_user_message("   ")


def test_message_id_is_unique():
    """生成されるメッセージIDがユニークであることをテスト"""
    message1 = Message.create_user_message("メッセージ1")
    message2 = Message.create_user_message("メッセージ2")

    assert message1.id != message2.id
