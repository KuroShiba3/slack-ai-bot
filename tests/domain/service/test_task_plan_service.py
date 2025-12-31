from uuid import uuid4

import pytest
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture

from src.domain.exception.chat_session_exception import UserMessageNotFoundError
from src.domain.exception.service_exception import UnknownAgentError
from src.domain.model import AgentName
from src.domain.model.chat_session import ChatSession
from src.domain.service.task_plan_service import TaskPlanningService


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def task_planning_service(mock_llm_client):
    """TaskPlanningServiceのインスタンス"""
    return TaskPlanningService(llm_client=mock_llm_client)


@pytest.fixture
def chat_session_with_messages():
    """メッセージを含むチャットセッション"""
    session = ChatSession.create(
        id="session-1", thread_id="thread-1", user_id="U12345", channel_id="C12345"
    )
    session.add_user_message("Pythonとは何ですか?")
    session.add_assistant_message("Pythonはプログラミング言語です")
    session.add_user_message("最新バージョンは?")
    return session


@pytest.fixture
def mock_task_plan_response():
    """LLMからのタスク計画レスポンスのモック"""

    class _Task(BaseModel):
        task_description: str = Field(description="タスクの内容")
        next_agent: str = Field(description="処理するエージェント")

    class _TaskPlan(BaseModel):
        tasks: list[_Task]
        reason: str

    return _TaskPlan(
        tasks=[
            _Task(
                task_description="Pythonの最新バージョンを検索",
                next_agent="web_search",
            ),
        ],
        reason="最新情報が必要なため検索エージェントを使用",
    )


@pytest.mark.asyncio
async def test_execute_creates_task_plan(
    task_planning_service,
    mock_llm_client,
    chat_session_with_messages,
    mock_task_plan_response,
):
    """タスク計画を生成するテスト"""
    mock_llm_client.generate_with_structured_output.return_value = (
        mock_task_plan_response
    )

    task_plan = await task_planning_service.execute(chat_session_with_messages)

    assert len(task_plan.tasks) == 1
    assert task_plan.tasks[0].description == "Pythonの最新バージョンを検索"
    assert task_plan.tasks[0].agent_name == AgentName.WEB_SEARCH
    assert mock_llm_client.generate_with_structured_output.called


@pytest.mark.asyncio
async def test_execute_with_multiple_tasks(
    task_planning_service, mock_llm_client, chat_session_with_messages
):
    """複数のタスクを持つ計画を生成するテスト"""
    from pydantic import BaseModel, Field

    class _Task(BaseModel):
        task_description: str = Field(description="タスクの内容")
        next_agent: str = Field(description="処理するエージェント")

    class _TaskPlan(BaseModel):
        tasks: list[_Task]
        reason: str

    mock_response = _TaskPlan(
        tasks=[
            _Task(
                task_description="Pythonの最新バージョンを検索",
                next_agent="web_search",
            ),
            _Task(
                task_description="Pythonの特徴を説明",
                next_agent="general_answer",
            ),
        ],
        reason="検索と一般回答の両方が必要",
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_response

    task_plan = await task_planning_service.execute(chat_session_with_messages)

    assert len(task_plan.tasks) == 2
    assert task_plan.tasks[0].agent_name == AgentName.WEB_SEARCH
    assert task_plan.tasks[1].agent_name == AgentName.GENERAL_ANSWER


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    task_planning_service,
    mock_llm_client,
    chat_session_with_messages,
    mock_task_plan_response,
):
    """システムプロンプトが含まれることをテスト"""
    mock_llm_client.generate_with_structured_output.return_value = (
        mock_task_plan_response
    )

    await task_planning_service.execute(chat_session_with_messages)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "実行可能な独立したサブタスクに分割" in messages[0].content
    assert "利用可能なエージェント" in messages[0].content


@pytest.mark.asyncio
async def test_execute_includes_conversation_history(
    task_planning_service,
    mock_llm_client,
    chat_session_with_messages,
    mock_task_plan_response,
):
    """会話履歴が含まれることをテスト"""
    mock_llm_client.generate_with_structured_output.return_value = (
        mock_task_plan_response
    )

    await task_planning_service.execute(chat_session_with_messages)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # システムプロンプト(1) + 会話履歴(3) + 最新リクエスト指示(1) = 5
    assert len(messages) == 5

    # 会話履歴が含まれていることを確認
    assert messages[1].content == "Pythonとは何ですか?"
    assert messages[2].content == "Pythonはプログラミング言語です"
    assert messages[3].content == "最新バージョンは?"


@pytest.mark.asyncio
async def test_execute_raises_error_when_no_user_message(
    task_planning_service, mock_llm_client
):
    """ユーザーメッセージがない場合にエラーを投げるテスト"""
    empty_session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    with pytest.raises(
        UserMessageNotFoundError, match="ユーザーメッセージが存在しません"
    ):
        await task_planning_service.execute(empty_session)


@pytest.mark.asyncio
async def test_execute_raises_error_for_unknown_agent(
    task_planning_service, mock_llm_client, chat_session_with_messages
):
    """未知のエージェントが指定された場合にエラーを投げるテスト"""
    from pydantic import BaseModel, Field

    class _Task(BaseModel):
        task_description: str = Field(description="タスクの内容")
        next_agent: str = Field(description="処理するエージェント")

    class _TaskPlan(BaseModel):
        tasks: list[_Task]
        reason: str

    mock_response = _TaskPlan(
        tasks=[
            _Task(
                task_description="タスク",
                next_agent="unknown_agent",  # 未知のエージェント
            ),
        ],
        reason="テスト",
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_response

    with pytest.raises(UnknownAgentError):
        await task_planning_service.execute(chat_session_with_messages)


@pytest.mark.asyncio
async def test_execute_creates_web_search_task(
    task_planning_service, mock_llm_client, chat_session_with_messages
):
    """Web検索タスクを作成するテスト"""
    from pydantic import BaseModel, Field

    class _Task(BaseModel):
        task_description: str = Field(description="タスクの内容")
        next_agent: str = Field(description="処理するエージェント")

    class _TaskPlan(BaseModel):
        tasks: list[_Task]
        reason: str

    mock_response = _TaskPlan(
        tasks=[
            _Task(
                task_description="最新のニュースを検索",
                next_agent="web_search",
            ),
        ],
        reason="最新情報が必要",
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_response

    task_plan = await task_planning_service.execute(chat_session_with_messages)

    assert task_plan.tasks[0].agent_name == AgentName.WEB_SEARCH
    assert task_plan.tasks[0].description == "最新のニュースを検索"
