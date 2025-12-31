from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.application.dto.feedback_usecase import FeedbackInput
from src.application.exception.usecase_exception import InvalidInputError
from src.application.usecase.feedback_usecase import FeedbackUseCase


@pytest.fixture
def mock_feedback_repository(mocker: MockerFixture):
    """FeedbackRepositoryのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def usecase(mock_feedback_repository):
    """FeedbackUseCaseのインスタンス"""
    return FeedbackUseCase(feedback_repository=mock_feedback_repository)


@pytest.fixture
def valid_good_feedback_input():
    """有効なGoodフィードバック入力DTO"""
    return FeedbackInput(
        message_id=str(uuid4()),
        feedback_type="good",
        user_id="U12345",
    )


@pytest.mark.asyncio
async def test_execute_raises_error_when_message_id_is_empty(
    usecase, mock_feedback_repository
):
    """message_idが空の場合にエラーを投げるテスト"""
    invalid_input = FeedbackInput(
        message_id="",
        feedback_type="good",
        user_id="U12345",
    )

    with pytest.raises(InvalidInputError, match="message_id"):
        await usecase.execute(invalid_input)

    # リポジトリが呼ばれていないことを確認
    assert not mock_feedback_repository.find_by_message_and_user.called


@pytest.mark.asyncio
async def test_execute_raises_error_when_feedback_type_is_empty(
    usecase, mock_feedback_repository
):
    """feedback_typeが空の場合にエラーを投げるテスト"""
    invalid_input = FeedbackInput(
        message_id=str(uuid4()),
        feedback_type="",
        user_id="U12345",
    )

    with pytest.raises(InvalidInputError, match="feedback_type"):
        await usecase.execute(invalid_input)

    # リポジトリが呼ばれていないことを確認
    assert not mock_feedback_repository.find_by_message_and_user.called


@pytest.mark.asyncio
async def test_execute_raises_error_when_user_id_is_empty(
    usecase, mock_feedback_repository
):
    """user_idが空の場合にエラーを投げるテスト"""
    invalid_input = FeedbackInput(
        message_id=str(uuid4()),
        feedback_type="good",
        user_id="",
    )

    with pytest.raises(InvalidInputError, match="user_id"):
        await usecase.execute(invalid_input)

    # リポジトリが呼ばれていないことを確認
    assert not mock_feedback_repository.find_by_message_and_user.called


@pytest.mark.asyncio
async def test_execute_calls_repository_with_correct_parameters(
    usecase, mock_feedback_repository, valid_good_feedback_input
):
    """リポジトリが正しいパラメータで呼ばれることをテスト"""
    mock_feedback_repository.find_by_message_and_user.return_value = None

    await usecase.execute(valid_good_feedback_input)

    # find_by_message_and_userが正しいパラメータで呼ばれたことを確認
    call_args = mock_feedback_repository.find_by_message_and_user.call_args
    assert str(call_args.kwargs["message_id"]) == valid_good_feedback_input.message_id
    assert call_args.kwargs["user_id"] == valid_good_feedback_input.user_id


@pytest.mark.asyncio
async def test_execute_converts_string_to_uuid(usecase, mock_feedback_repository):
    """文字列のmessage_idがUUIDに変換されることをテスト"""
    message_id = uuid4()
    input_dto = FeedbackInput(
        message_id=str(message_id),  # 文字列として渡す
        feedback_type="good",
        user_id="U12345",
    )

    mock_feedback_repository.find_by_message_and_user.return_value = None

    await usecase.execute(input_dto)

    # 保存されたフィードバックのmessage_idがUUIDであることを確認
    save_call_args = mock_feedback_repository.save.call_args
    saved_feedback = save_call_args[0][0]
    assert saved_feedback.message_id == message_id
