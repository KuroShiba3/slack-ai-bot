from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.application.dto.answer_to_user_request_usecase import (
    AnswerToUserRequestInput,
    AnswerToUserRequestOutput,
)
from src.application.exception.base import ApplicationException
from src.domain.exception.base import DomainException
from src.infrastructure.exception.base import InfrastructureException
from src.presentation.controllers.slack_message_controller import (
    SlackMessageController,
)
from src.presentation.dto.slack_request_dto import SlackRequestDTO
from src.presentation.exception.base import PresentationException


@pytest.fixture
def mock_use_case(mocker: MockerFixture):
    """AnswerToUserRequestUseCaseのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def mock_mapper(mocker: MockerFixture):
    """SlackRequestMapperのモック"""
    return mocker.Mock()


@pytest.fixture
def mock_slack_service(mocker: MockerFixture):
    """SlackMessageServiceのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def mock_ack(mocker: MockerFixture):
    """Ackのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def controller(mock_use_case, mock_mapper, mock_slack_service):
    """SlackMessageControllerのインスタンス"""
    # クラス変数をリセット
    SlackMessageController._processed_events = set()
    return SlackMessageController(
        use_case=mock_use_case,
        mapper=mock_mapper,
        slack_service=mock_slack_service,
    )


@pytest.fixture
def valid_event():
    """有効なSlackイベント"""
    return {
        "text": "こんにちは",
        "user": "U12345",
        "channel": "C12345",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
    }


@pytest.fixture
def valid_slack_dto():
    """有効なSlackRequestDTO"""
    return SlackRequestDTO(
        text="こんにちは",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
    )


@pytest.fixture
def valid_body(valid_event):
    """有効なリクエストボディ"""
    return {"event": valid_event}


@pytest.mark.asyncio
async def test_execute_processes_valid_message(
    controller,
    mock_use_case,
    mock_mapper,
    mock_slack_service,
    mock_ack,
    valid_body,
    valid_event,
    valid_slack_dto,
):
    """有効なメッセージを処理するテスト"""
    message_id = uuid4()
    app_input = AnswerToUserRequestInput(
        user_message="こんにちは",
        context={"conversation_id": "C12345_1234567890.123456"},
    )
    app_output = AnswerToUserRequestOutput(
        answer="こんにちは！元気ですか？", message_id=message_id
    )

    mock_mapper.from_event.return_value = valid_slack_dto
    mock_mapper.is_bot_message.return_value = False
    mock_mapper.to_application_input.return_value = app_input
    mock_use_case.execute.return_value = app_output

    await controller.execute(mock_ack, valid_body)

    # ackが呼ばれたことを確認
    assert mock_ack.called

    # Mapperが呼ばれたことを確認
    mock_mapper.from_event.assert_called_with(valid_event)
    mock_mapper.is_bot_message.assert_called_with(valid_slack_dto)
    mock_mapper.to_application_input.assert_called_with(valid_slack_dto)

    # UseCaseが呼ばれたことを確認
    assert mock_use_case.execute.called

    # Slackサービスが呼ばれたことを確認
    assert mock_slack_service.add_reaction.called
    assert mock_slack_service.send_message.called
    assert mock_slack_service.remove_reaction.called


@pytest.mark.asyncio
async def test_execute_skips_bot_message(
    controller,
    mock_use_case,
    mock_mapper,
    mock_slack_service,
    mock_ack,
    valid_body,
    valid_event,
):
    """ボットメッセージをスキップするテスト"""
    bot_dto = SlackRequestDTO(
        text="ボットメッセージ",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        event_id="1234567890.123456",
        bot_id="B12345",
    )

    mock_mapper.from_event.return_value = bot_dto
    mock_mapper.is_bot_message.return_value = True

    await controller.execute(mock_ack, valid_body)

    # ackは呼ばれる
    assert mock_ack.called

    # ボットメッセージなのでUseCaseは呼ばれない
    assert not mock_use_case.execute.called

    # リアクションも追加されない
    assert not mock_slack_service.add_reaction.called


@pytest.mark.asyncio
async def test_execute_skips_duplicate_event(
    controller,
    mock_use_case,
    mock_mapper,
    mock_ack,
    valid_body,
    valid_slack_dto,
):
    """重複イベントをスキップするテスト"""
    mock_mapper.from_event.return_value = valid_slack_dto
    mock_mapper.is_bot_message.return_value = False

    # 1回目の処理
    await controller.execute(mock_ack, valid_body)

    # 2回目の処理（同じevent_id）
    await controller.execute(mock_ack, valid_body)

    # UseCaseは1回だけ呼ばれる
    assert mock_use_case.execute.call_count == 1


@pytest.mark.asyncio
async def test_execute_adds_and_removes_reaction(
    controller,
    mock_use_case,
    mock_mapper,
    mock_slack_service,
    mock_ack,
    valid_body,
    valid_slack_dto,
):
    """リアクションの追加と削除を行うテスト"""
    message_id = uuid4()
    app_input = AnswerToUserRequestInput(
        user_message="こんにちは",
        context={"conversation_id": "C12345_1234567890.123456"},
    )
    app_output = AnswerToUserRequestOutput(answer="回答", message_id=message_id)

    mock_mapper.from_event.return_value = valid_slack_dto
    mock_mapper.is_bot_message.return_value = False
    mock_mapper.to_application_input.return_value = app_input
    mock_use_case.execute.return_value = app_output

    await controller.execute(mock_ack, valid_body)

    # リアクション追加が呼ばれたことを確認
    mock_slack_service.add_reaction.assert_called_once_with(
        "C12345", "1234567890.123456", "eyes"
    )

    # リアクション削除が呼ばれたことを確認
    mock_slack_service.remove_reaction.assert_called_once_with(
        "C12345", "1234567890.123456", "eyes"
    )


@pytest.mark.asyncio
async def test_execute_sends_message_to_thread(
    controller,
    mock_use_case,
    mock_mapper,
    mock_slack_service,
    mock_ack,
    valid_event,
):
    """スレッドにメッセージを送信するテスト"""
    message_id = uuid4()
    thread_dto = SlackRequestDTO(
        text="スレッド返信",
        user_id="U12345",
        channel_id="C12345",
        message_ts="1234567891.123456",
        thread_ts="1234567890.123456",
        event_id="1234567891.123456",
    )
    app_input = AnswerToUserRequestInput(
        user_message="スレッド返信",
        context={"conversation_id": "C12345_1234567890.123456"},
    )
    app_output = AnswerToUserRequestOutput(answer="回答", message_id=message_id)

    mock_mapper.from_event.return_value = thread_dto
    mock_mapper.is_bot_message.return_value = False
    mock_mapper.to_application_input.return_value = app_input
    mock_use_case.execute.return_value = app_output

    body = {"event": valid_event}
    await controller.execute(mock_ack, body)

    # スレッドTSが正しく渡されることを確認
    call_args = mock_slack_service.send_message.call_args
    assert call_args.kwargs["thread_ts"] == "1234567890.123456"
