from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.application.dto.answer_to_user_request_usecase import (
    AnswerToUserRequestInput,
)
from src.application.exception.usecase_exception import InvalidInputError
from src.application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from src.domain.model import Task, TaskPlan, WorkflowResult


@pytest.fixture
def mock_workflow_service(mocker: MockerFixture):
    """WorkflowServiceのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def mock_chat_session_repository(mocker: MockerFixture):
    """ChatSessionRepositoryのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def usecase(mock_workflow_service, mock_chat_session_repository):
    """AnswerToUserRequestUseCaseのインスタンス"""
    return AnswerToUserRequestUseCase(
        workflow_service=mock_workflow_service,
        chat_session_repository=mock_chat_session_repository,
    )


@pytest.fixture
def valid_input():
    """有効な入力DTO"""
    return AnswerToUserRequestInput(
        user_message="Pythonについて教えて",
        context={
            "conversation_id": "conv-123",
            "thread_ts": "thread-456",
            "user_id": "U12345",
            "channel_id": "C12345",
        },
    )


@pytest.fixture
def workflow_result():
    """ワークフロー実行結果のモック"""
    message_id = uuid4()
    task = Task.create_general_answer("Pythonについて説明")
    task.complete("Pythonはプログラミング言語です")
    task_plan = TaskPlan.create(message_id=message_id, tasks=[task])

    return WorkflowResult(
        answer="Pythonはプログラミング言語です",
        task_plan=task_plan,
    )


@pytest.mark.asyncio
async def test_execute_raises_error_when_user_message_is_empty(
    usecase, mock_chat_session_repository
):
    """ユーザーメッセージが空の場合にエラーを投げるテスト"""
    invalid_input = AnswerToUserRequestInput(
        user_message="",
        context={"conversation_id": "conv-123"},
    )

    with pytest.raises(InvalidInputError, match="user_message"):
        await usecase.execute(invalid_input)

    # リポジトリが呼ばれていないことを確認
    assert not mock_chat_session_repository.find_by_id.called


@pytest.mark.asyncio
async def test_execute_raises_error_when_conversation_id_is_missing(
    usecase, mock_chat_session_repository
):
    """conversation_idがない場合にエラーを投げるテスト"""
    invalid_input = AnswerToUserRequestInput(
        user_message="質問",
        context={},  # conversation_idなし
    )

    with pytest.raises(InvalidInputError, match="conversation_id"):
        await usecase.execute(invalid_input)

    # リポジトリが呼ばれていないことを確認
    assert not mock_chat_session_repository.find_by_id.called


@pytest.mark.asyncio
async def test_execute_passes_context_to_workflow(
    usecase,
    mock_workflow_service,
    mock_chat_session_repository,
    valid_input,
    workflow_result,
):
    """コンテキストがワークフローサービスに渡されることをテスト"""
    mock_chat_session_repository.find_by_id.return_value = None
    mock_workflow_service.execute.return_value = workflow_result

    await usecase.execute(valid_input)

    call_args = mock_workflow_service.execute.call_args
    context_arg = call_args[0][1]

    assert context_arg == valid_input.context


@pytest.mark.asyncio
async def test_execute_creates_session_with_correct_attributes(
    usecase,
    mock_workflow_service,
    mock_chat_session_repository,
    workflow_result,
):
    """正しい属性でセッションが作成されることをテスト"""
    input_dto = AnswerToUserRequestInput(
        user_message="質問",
        context={
            "conversation_id": "conv-999",
            "thread_ts": "thread-888",
            "user_id": "U99999",
            "channel_id": "C99999",
        },
    )

    mock_chat_session_repository.find_by_id.return_value = None
    mock_workflow_service.execute.return_value = workflow_result

    await usecase.execute(input_dto)

    # ワークフローに渡されたセッションを確認
    call_args = mock_workflow_service.execute.call_args
    session_arg = call_args[0][0]

    assert session_arg.id == "conv-999"
    assert session_arg.thread_id == "thread-888"
    assert session_arg.user_id == "U99999"
    assert session_arg.channel_id == "C99999"
