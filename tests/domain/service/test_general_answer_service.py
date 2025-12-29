import pytest
from pytest_mock import MockerFixture

from src.domain.model.chat_session import ChatSession
from src.domain.model.message import Message
from src.domain.model.task import Task, TaskStatus
from src.domain.service.general_answer_service import GeneralAnswerService


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def general_answer_service(mock_llm_client):
    """GeneralAnswerServiceのインスタンス"""
    return GeneralAnswerService(llm_client=mock_llm_client)


@pytest.fixture
def chat_session_with_messages():
    """メッセージを含むチャットセッション"""
    session = ChatSession.create(
        id="session-1", thread_id="thread-1", user_id="U12345", channel_id="C12345"
    )
    session.add_user_message("Pythonとは何ですか?")
    session.add_assistant_message("Pythonは...")
    session.add_user_message("もっと詳しく教えて")
    return session


@pytest.fixture
def general_answer_task():
    """一般回答タスク"""
    return Task.create_general_answer("Pythonの特徴を説明してください")


@pytest.mark.asyncio
async def test_execute_generates_answer_and_completes_task(
    general_answer_service,
    mock_llm_client,
    chat_session_with_messages,
    general_answer_task,
):
    """回答を生成してタスクを完了するテスト"""
    mock_llm_client.generate.return_value = "Pythonは読みやすいプログラミング言語です"

    await general_answer_service.execute(
        chat_session_with_messages, general_answer_task
    )

    # LLMが呼ばれたことを確認
    assert mock_llm_client.generate.called
    assert mock_llm_client.generate.call_count == 1

    # タスクが完了していることを確認
    assert general_answer_task.status == TaskStatus.COMPLETED
    assert general_answer_task.result == "Pythonは読みやすいプログラミング言語です"


@pytest.mark.asyncio
async def test_execute_adds_attempt_to_task_log(
    general_answer_service,
    mock_llm_client,
    chat_session_with_messages,
    general_answer_task,
):
    """試行ログに記録されることをテスト"""
    mock_llm_client.generate.return_value = "回答内容"

    await general_answer_service.execute(
        chat_session_with_messages, general_answer_task
    )

    # タスクログに試行が記録されていることを確認
    assert len(general_answer_task.task_log.attempts) == 1
    assert general_answer_task.task_log.attempts[0].response == "回答内容"


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    general_answer_service,
    mock_llm_client,
    chat_session_with_messages,
    general_answer_task,
):
    """システムプロンプトが含まれることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await general_answer_service.execute(
        chat_session_with_messages, general_answer_task
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "あなたは親切なアシスタントAI" in messages[0].content
    assert "Slack mrkdwn形式" in messages[0].content


@pytest.mark.asyncio
async def test_execute_includes_conversation_history(
    general_answer_service,
    mock_llm_client,
    chat_session_with_messages,
    general_answer_task,
):
    """会話履歴が含まれることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await general_answer_service.execute(
        chat_session_with_messages, general_answer_task
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # システムプロンプト(1) + 会話履歴全体(3メッセージ) + タスクプロンプト(1) = 5
    # 注: GeneralAnswerServiceは全会話履歴を含める（最新のユーザーメッセージも含む）
    assert len(messages) == 5

    # 会話履歴全体が含まれていることを確認
    assert messages[1].content == "Pythonとは何ですか?"
    assert messages[2].content == "Pythonは..."
    assert messages[3].content == "もっと詳しく教えて"  # 最新のユーザーメッセージも含まれる


@pytest.mark.asyncio
async def test_execute_includes_task_description(
    general_answer_service,
    mock_llm_client,
    chat_session_with_messages,
    general_answer_task,
):
    """タスクの説明が含まれることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await general_answer_service.execute(
        chat_session_with_messages, general_answer_task
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最後のメッセージにタスクの説明が含まれていることを確認
    last_message = messages[-1]
    assert "Pythonの特徴を説明してください" in last_message.content


@pytest.mark.asyncio
async def test_build_task_prompt_format(general_answer_service):
    """_build_task_promptが正しいフォーマットを生成することをテスト"""
    task_description = "Pythonの特徴を説明してください"

    prompt = general_answer_service._build_task_prompt(task_description)

    assert "## 現在の日付:" in prompt
    assert "## タスク:" in prompt
    assert task_description in prompt
    assert "上記のタスクについて回答してください" in prompt
