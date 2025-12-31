import json
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.application.dto.feedback_usecase import FeedbackInput
from src.presentation.controllers.slack_feedback_controller import (
    SlackFeedbackController,
)


@pytest.fixture
def mock_feedback_usecase(mocker: MockerFixture):
    """FeedbackUseCaseのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def mock_ack(mocker: MockerFixture):
    """Ackのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def controller(mock_feedback_usecase):
    """SlackFeedbackControllerのインスタンス"""
    return SlackFeedbackController(feedback_usecase=mock_feedback_usecase)


@pytest.fixture
def valid_feedback_body():
    """有効なフィードバックリクエストボディ"""
    message_id = str(uuid4())
    return {
        "user": {"id": "U12345"},
        "actions": [
            {
                "value": json.dumps(
                    {
                        "message_id": message_id,
                        "type": "good",
                    }
                )
            }
        ],
    }


@pytest.mark.asyncio
async def test_execute_with_valid_good_feedback(
    controller, mock_feedback_usecase, mock_ack, valid_feedback_body
):
    """有効なGoodフィードバックを処理するテスト"""
    await controller.execute(mock_ack, valid_feedback_body)

    # ackが呼ばれたことを確認
    assert mock_ack.called

    # UseCaseが呼ばれたことを確認
    assert mock_feedback_usecase.execute.called
    call_args = mock_feedback_usecase.execute.call_args
    input_dto = call_args[0][0]

    assert isinstance(input_dto, FeedbackInput)
    assert input_dto.user_id == "U12345"
    assert input_dto.feedback_type == "good"


@pytest.mark.asyncio
async def test_execute_with_valid_bad_feedback(
    controller, mock_feedback_usecase, mock_ack
):
    """有効なBadフィードバックを処理するテスト"""
    message_id = str(uuid4())
    body = {
        "user": {"id": "U12345"},
        "actions": [
            {
                "value": json.dumps(
                    {
                        "message_id": message_id,
                        "type": "bad",
                    }
                )
            }
        ],
    }

    await controller.execute(mock_ack, body)

    # UseCaseが呼ばれたことを確認
    call_args = mock_feedback_usecase.execute.call_args
    input_dto = call_args[0][0]

    assert input_dto.feedback_type == "bad"


@pytest.mark.asyncio
async def test_parse_feedback_request_returns_correct_dto(controller):
    """_parse_feedback_requestが正しいDTOを返すテスト"""
    message_id = str(uuid4())
    body = {
        "user": {"id": "U12345"},
        "actions": [
            {
                "value": json.dumps(
                    {
                        "message_id": message_id,
                        "type": "good",
                    }
                )
            }
        ],
    }

    dto = controller._parse_feedback_request(body)

    assert dto.message_id == message_id
    assert dto.feedback_type == "good"
    assert dto.user_id == "U12345"
