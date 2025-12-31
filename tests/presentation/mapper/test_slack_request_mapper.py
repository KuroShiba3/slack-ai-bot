import pytest

from src.presentation.dto.slack_request_dto import SlackRequestDTO
from src.presentation.exception.request_exception import InvalidRequestError
from src.presentation.mapper.slack_request_mapper import SlackRequestMapper


def test_from_event_with_valid_data():
    """有効なイベントデータからDTOを生成するテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.text == "こんにちは"
    assert dto.user_id == "U12345"
    assert dto.channel_id == "C12345"
    assert dto.message_ts == "1234567890.123456"
    assert dto.event_id == "1234567890.123456"
    assert dto.thread_ts is None
    assert dto.bot_id is None


def test_from_event_with_thread():
    """スレッド付きイベントからDTOを生成するテスト"""
    event = {
        "text": "スレッド返信",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567891.123456",
        "thread_ts": "1234567890.123456",
        "event_ts": "1234567891.123456",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.thread_ts == "1234567890.123456"
    assert dto.message_ts == "1234567891.123456"


def test_from_event_with_bot_id():
    """bot_id付きイベントからDTOを生成するテスト"""
    event = {
        "text": "ボットメッセージ",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
        "bot_id": "B12345",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.bot_id == "B12345"


def test_from_event_removes_mention():
    """メンションが削除されることをテスト"""
    event = {
        "text": "<@U12345> こんにちは",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.text == "こんにちは"
    assert "<@U12345>" not in dto.text


def test_from_event_raises_error_when_text_is_missing():
    """textが欠けている場合にエラーを投げるテスト"""
    event = {
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="テキスト"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_text_is_empty():
    """textが空の場合にエラーを投げるテスト"""
    event = {
        "text": "",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="テキスト"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_text_is_only_whitespace():
    """textが空白のみの場合にエラーを投げるテスト"""
    event = {
        "text": "   ",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match=r"text\(空のメッセージ\)"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_text_is_only_mention():
    """textがメンションのみの場合にエラーを投げるテスト"""
    event = {
        "text": "<@U12345>",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match=r"text\(空のメッセージ\)"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_user_is_missing():
    """userが欠けている場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="ユーザーID"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_user_format_is_invalid():
    """userの形式が不正な場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "user": "INVALID",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="不正な形式"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_channel_is_missing():
    """channelが欠けている場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="チャンネルID"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_channel_format_is_invalid():
    """channelの形式が不正な場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "INVALID",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="不正な形式"):
        SlackRequestMapper.from_event(event)


def test_from_event_accepts_dm_channel():
    """DMチャンネル(D始まり)を受け入れるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "D12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.channel_id == "D12345"


def test_from_event_accepts_group_channel():
    """グループチャンネル(G始まり)を受け入れるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "G12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }

    dto = SlackRequestMapper.from_event(event)

    assert dto.channel_id == "G12345"


def test_from_event_raises_error_when_ts_is_missing():
    """tsが欠けている場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "C12345",
        "event_ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="タイムスタンプ"):
        SlackRequestMapper.from_event(event)


def test_from_event_raises_error_when_event_ts_is_missing():
    """event_tsが欠けている場合にエラーを投げるテスト"""
    event = {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
    }

    with pytest.raises(InvalidRequestError, match="イベントタイムスタンプ"):
        SlackRequestMapper.from_event(event)


def test_to_application_input_without_thread():
    """スレッドなしの場合のアプリケーション入力変換テスト"""
    slack_dto = SlackRequestDTO(
        text="こんにちは",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
    )

    app_input = SlackRequestMapper.to_application_input(slack_dto)

    assert app_input.user_message == "こんにちは"
    assert app_input.context["user_id"] == "U12345"
    assert app_input.context["channel_id"] == "C12345"
    assert app_input.context["thread_ts"] == "1234567890.123456"
    assert app_input.context["message_ts"] == "1234567890.123456"
    assert app_input.context["conversation_id"] == "C12345_1234567890.123456"


def test_to_application_input_with_thread():
    """スレッドありの場合のアプリケーション入力変換テスト"""
    slack_dto = SlackRequestDTO(
        text="スレッド返信",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567891.123456",
        thread_ts="1234567890.123456",
        event_id="1234567891.123456",
    )

    app_input = SlackRequestMapper.to_application_input(slack_dto)

    assert app_input.context["thread_ts"] == "1234567890.123456"
    assert app_input.context["message_ts"] == "1234567891.123456"
    assert app_input.context["conversation_id"] == "C12345_1234567890.123456"


def test_to_application_input_conversation_id_uses_message_ts_when_no_thread():
    """スレッドがない場合、conversation_idにmessage_tsを使用するテスト"""
    slack_dto = SlackRequestDTO(
        text="メッセージ",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
        thread_ts=None,
    )

    app_input = SlackRequestMapper.to_application_input(slack_dto)

    assert app_input.context["conversation_id"] == "C12345_1234567890.123456"


def test_is_bot_message_returns_true_when_bot_id_exists():
    """bot_idが存在する場合にTrueを返すテスト"""
    slack_dto = SlackRequestDTO(
        text="ボットメッセージ",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
        bot_id="B12345",
    )

    assert SlackRequestMapper.is_bot_message(slack_dto) is True


def test_is_bot_message_returns_false_when_bot_id_is_none():
    """bot_idがNoneの場合にFalseを返すテスト"""
    slack_dto = SlackRequestDTO(
        text="ユーザーメッセージ",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
        bot_id=None,
    )

    assert SlackRequestMapper.is_bot_message(slack_dto) is False
