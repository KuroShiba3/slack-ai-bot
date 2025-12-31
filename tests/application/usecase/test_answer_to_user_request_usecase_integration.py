from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.application.dto.answer_to_user_request_usecase import (
    AnswerToUserRequestInput,
)
from src.application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from src.domain.model import Task, TaskPlan, WorkflowResult
from tests.infrastructure.repository.in_memory_chat_session_repository import (
    InMemoryChatSessionRepository,
)


@pytest.fixture
def repository():
    """インメモリリポジトリ"""
    repo = InMemoryChatSessionRepository()
    yield repo
    repo.clear()


@pytest.fixture
def mock_workflow_service(mocker: MockerFixture):
    """WorkflowServiceのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def usecase(mock_workflow_service, repository):
    """AnswerToUserRequestUseCaseのインスタンス"""
    return AnswerToUserRequestUseCase(
        workflow_service=mock_workflow_service,
        chat_session_repository=repository,
    )


@pytest.mark.asyncio
async def test_first_message_creates_new_session(
    usecase, mock_workflow_service, repository
):
    """初回メッセージで新しいセッションが作成されるテスト"""
    message_id = uuid4()
    task = Task.create_general_answer("Pythonについて説明")
    task.complete("Pythonはプログラミング言語です")
    task_plan = TaskPlan.create(message_id=message_id, tasks=[task])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="Pythonはプログラミング言語です", task_plan=task_plan
    )

    input_dto = AnswerToUserRequestInput(
        user_message="Pythonについて教えて",
        context={
            "conversation_id": "conv-123",
            "user_id": "U12345",
            "channel_id": "C12345",
            "thread_ts": "1234567890.123456",
        },
    )

    await usecase.execute(input_dto)

    # セッションが保存されていることを確認
    saved_session = await repository.find_by_id("conv-123")
    assert saved_session is not None
    assert saved_session.id == "conv-123"
    assert saved_session.user_id == "U12345"
    assert saved_session.channel_id == "C12345"

    # メッセージが保存されていることを確認
    assert len(saved_session.messages) == 2
    assert saved_session.messages[0].content == "Pythonについて教えて"
    assert saved_session.messages[0].role.value == "user"
    assert saved_session.messages[1].content == "Pythonはプログラミング言語です"
    assert saved_session.messages[1].role.value == "assistant"

    # タスクプランが保存されていることを確認
    assert len(saved_session.task_plans) == 1
    # エンティティなのでIDで比較
    assert saved_session.task_plans[0].id == task_plan.id
    assert saved_session.task_plans[0].message_id == task_plan.message_id
    assert len(saved_session.task_plans[0].tasks) == len(task_plan.tasks)


@pytest.mark.asyncio
async def test_second_message_updates_existing_session(
    usecase, mock_workflow_service, repository
):
    """2回目のメッセージで既存セッションが更新されるテスト"""
    # 1回目のメッセージ
    message_id1 = uuid4()
    task1 = Task.create_general_answer("Pythonについて説明")
    task1.complete("Pythonはプログラミング言語です")
    task_plan1 = TaskPlan.create(message_id=message_id1, tasks=[task1])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="Pythonはプログラミング言語です", task_plan=task_plan1
    )

    input_dto1 = AnswerToUserRequestInput(
        user_message="Pythonについて教えて",
        context={
            "conversation_id": "conv-123",
            "user_id": "U12345",
            "channel_id": "C12345",
            "thread_ts": "1234567890.123456",
        },
    )

    await usecase.execute(input_dto1)

    # 2回目のメッセージ
    message_id2 = uuid4()
    task2 = Task.create_general_answer("バージョンについて説明")
    task2.complete("最新バージョンは3.13です")
    task_plan2 = TaskPlan.create(message_id=message_id2, tasks=[task2])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="最新バージョンは3.13です", task_plan=task_plan2
    )

    input_dto2 = AnswerToUserRequestInput(
        user_message="最新バージョンは?",
        context={
            "conversation_id": "conv-123",
            "user_id": "U12345",
            "channel_id": "C12345",
            "thread_ts": "1234567890.123456",
        },
    )

    await usecase.execute(input_dto2)

    # セッションが更新されていることを確認
    saved_session = await repository.find_by_id("conv-123")
    assert saved_session is not None

    # メッセージが4つになっていることを確認
    assert len(saved_session.messages) == 4
    assert saved_session.messages[0].content == "Pythonについて教えて"
    assert saved_session.messages[1].content == "Pythonはプログラミング言語です"
    assert saved_session.messages[2].content == "最新バージョンは?"
    assert saved_session.messages[3].content == "最新バージョンは3.13です"

    # タスクプランが2つになっていることを確認
    assert len(saved_session.task_plans) == 2


@pytest.mark.asyncio
async def test_multiple_conversations_are_separate(
    usecase, mock_workflow_service, repository
):
    """複数の会話が個別に管理されることをテスト"""
    message_id1 = uuid4()
    task1 = Task.create_general_answer("説明")
    task1.complete("回答A")
    task_plan1 = TaskPlan.create(message_id=message_id1, tasks=[task1])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="回答A", task_plan=task_plan1
    )

    # 会話1
    input_dto1 = AnswerToUserRequestInput(
        user_message="質問A",
        context={
            "conversation_id": "conv-A",
            "user_id": "U12345",
            "channel_id": "C12345",
            "thread_ts": "1111111111.111111",
        },
    )

    await usecase.execute(input_dto1)

    message_id2 = uuid4()
    task2 = Task.create_general_answer("説明")
    task2.complete("回答B")
    task_plan2 = TaskPlan.create(message_id=message_id2, tasks=[task2])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="回答B", task_plan=task_plan2
    )

    # 会話2
    input_dto2 = AnswerToUserRequestInput(
        user_message="質問B",
        context={
            "conversation_id": "conv-B",
            "user_id": "U67890",
            "channel_id": "C67890",
            "thread_ts": "2222222222.222222",
        },
    )

    await usecase.execute(input_dto2)

    # 2つの会話が個別に保存されていることを確認
    session_a = await repository.find_by_id("conv-A")
    session_b = await repository.find_by_id("conv-B")

    assert session_a is not None
    assert session_b is not None

    assert session_a.user_id == "U12345"
    assert session_b.user_id == "U67890"

    assert session_a.messages[0].content == "質問A"
    assert session_b.messages[0].content == "質問B"


@pytest.mark.asyncio
async def test_workflow_result_is_saved_correctly(
    usecase, mock_workflow_service, repository
):
    """ワークフロー結果が正しく保存されることをテスト"""
    message_id = uuid4()

    # 複数のタスクを持つタスクプラン
    task1 = Task.create_web_search("検索タスク")
    task1.complete("検索結果")
    task2 = Task.create_general_answer("一般回答タスク")
    task2.complete("一般回答")
    task_plan = TaskPlan.create(message_id=message_id, tasks=[task1, task2])

    mock_workflow_service.execute.return_value = WorkflowResult(
        answer="統合された回答", task_plan=task_plan
    )

    input_dto = AnswerToUserRequestInput(
        user_message="質問",
        context={
            "conversation_id": "conv-123",
            "user_id": "U12345",
            "channel_id": "C12345",
            "thread_ts": "1234567890.123456",
        },
    )

    await usecase.execute(input_dto)

    # セッションを取得
    saved_session = await repository.find_by_id("conv-123")

    # タスクプランが正しく保存されていることを確認
    assert len(saved_session.task_plans) == 1
    assert len(saved_session.task_plans[0].tasks) == 2

    # タスクの詳細が保存されていることを確認
    saved_task1 = saved_session.task_plans[0].tasks[0]
    saved_task2 = saved_session.task_plans[0].tasks[1]

    assert saved_task1.description == "検索タスク"
    assert saved_task1.result == "検索結果"
    assert saved_task2.description == "一般回答タスク"
    assert saved_task2.result == "一般回答"
