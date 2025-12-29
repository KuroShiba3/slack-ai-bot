from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.domain.model.chat_session import ChatSession
from src.domain.model.message import Message
from src.domain.model.task import Task
from src.domain.model.task_plan import TaskPlan
from src.domain.service.answer_generation_service import AnswerGenerationService


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def answer_service(mock_llm_client):
    """AnswerGenerationServiceのインスタンス"""
    return AnswerGenerationService(llm_client=mock_llm_client)


@pytest.fixture
def chat_session_with_messages():
    """メッセージを含むチャットセッション"""
    session = ChatSession.create(
        id="session-1", thread_id="thread-1", user_id="U12345", channel_id="C12345"
    )
    session.add_user_message("Pythonの最新バージョンは?")
    session.add_assistant_message("検索中です...")
    session.add_user_message("詳しく教えて")
    return session


@pytest.fixture
def task_plan_with_completed_tasks():
    """完了したタスクを含むタスク計画"""
    message_id = uuid4()

    task1 = Task.create_web_search("Pythonの最新バージョンを検索")
    task1.complete("Python 3.13がリリースされました")

    task2 = Task.create_general_answer("Pythonの特徴を説明")
    task2.complete("Pythonは読みやすく、書きやすいプログラミング言語です")

    return TaskPlan.create(message_id=message_id, tasks=[task1, task2])


@pytest.mark.asyncio
async def test_execute_generates_answer(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """最終回答を生成するテスト"""
    mock_llm_client.generate.return_value = "統合された回答です"

    result = await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    assert result.content == "統合された回答です"
    assert mock_llm_client.generate.called
    assert mock_llm_client.generate.call_count == 1


@pytest.mark.asyncio
async def test_execute_uses_latest_user_message(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """最新のユーザーメッセージを使用することをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    # generate()に渡されたメッセージを取得
    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最後のユーザーメッセージに最新の質問が含まれていることを確認
    last_user_message = messages[-1]
    assert "詳しく教えて" in last_user_message.content


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """システムプロンプトが含まれることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "タスクの実行結果を統合" in messages[0].content


@pytest.mark.asyncio
async def test_execute_includes_task_results(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """タスク実行結果が含まれることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最後のユーザーメッセージにタスク結果が含まれていることを確認
    last_user_message = messages[-1]
    assert "タスクの実行結果" in last_user_message.content
    assert "Python 3.13がリリースされました" in last_user_message.content
    assert "Pythonは読みやすく" in last_user_message.content


@pytest.mark.asyncio
async def test_execute_excludes_latest_user_message_from_history(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """会話履歴から最新のユーザーメッセージが除外されることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # システムプロンプト + 会話履歴(最新除く) + 新しいプロンプト = 合計メッセージ数
    # システムプロンプト(1) + 最初のユーザーメッセージ(1) + アシスタント(1) + 新しいプロンプト(1) = 4
    assert len(messages) == 4

    # 会話履歴に含まれるのは最初のユーザーメッセージとアシスタントメッセージのみ
    assert messages[1].content == "Pythonの最新バージョンは?"
    assert messages[2].content == "検索中です..."


@pytest.mark.asyncio
async def test_execute_raises_error_when_no_user_message(
    answer_service, mock_llm_client, task_plan_with_completed_tasks
):
    """ユーザーメッセージがない場合にエラーを投げるテスト"""
    empty_session = ChatSession.create(
        id="session-1", thread_id=None, user_id="U12345", channel_id="C12345"
    )

    with pytest.raises(ValueError, match="最終回答を生成するにはユーザーメッセージが必要です"):
        await answer_service.execute(empty_session, task_plan_with_completed_tasks)


@pytest.mark.asyncio
async def test_execute_with_single_task(
    answer_service, mock_llm_client, chat_session_with_messages
):
    """単一タスクの結果から回答を生成するテスト"""
    mock_llm_client.generate.return_value = "単一タスクの回答"

    task = Task.create_web_search("検索タスク")
    task.complete("検索結果")
    task_plan = TaskPlan.create(message_id=uuid4(), tasks=[task])

    result = await answer_service.execute(chat_session_with_messages, task_plan)

    assert result.content == "単一タスクの回答"

    # タスク結果が含まれていることを確認
    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]
    last_message = messages[-1]
    assert "検索結果" in last_message.content


@pytest.mark.asyncio
async def test_build_human_prompt_format(answer_service):
    """_build_human_promptが正しいフォーマットを生成することをテスト"""
    user_question = "Pythonについて教えて"
    task_results = "タスク結果のサンプル"

    prompt = answer_service._build_human_prompt(user_question, task_results)

    assert "## ユーザーの質問:" in prompt
    assert user_question in prompt
    assert "## タスクの実行結果:" in prompt
    assert task_results in prompt
    assert "包括的な回答を生成してください" in prompt
    assert "URLは、一字一句完全にコピー" in prompt


@pytest.mark.asyncio
async def test_execute_with_empty_task_results(
    answer_service, mock_llm_client, chat_session_with_messages
):
    """タスク結果が空の場合のテスト"""
    mock_llm_client.generate.return_value = "回答"

    # 結果が設定されていないタスク
    task = Task.create_general_answer("タスク")
    # task.complete()を呼ばない（結果なし）
    task_plan = TaskPlan.create(message_id=uuid4(), tasks=[task])

    result = await answer_service.execute(chat_session_with_messages, task_plan)

    assert result.content == "回答"

    # "完了したタスクがありません"というメッセージが含まれることを確認
    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]
    last_message = messages[-1]
    assert "完了したタスクがありません" in last_message.content


@pytest.mark.asyncio
async def test_execute_returns_assistant_message(
    answer_service, mock_llm_client, chat_session_with_messages, task_plan_with_completed_tasks
):
    """返されるメッセージがアシスタントメッセージであることをテスト"""
    mock_llm_client.generate.return_value = "アシスタントの回答"

    result = await answer_service.execute(
        chat_session_with_messages, task_plan_with_completed_tasks
    )

    assert result.role.value == "assistant"


@pytest.mark.asyncio
async def test_execute_with_multiline_task_results(
    answer_service, mock_llm_client, chat_session_with_messages
):
    """複数行のタスク結果を処理できることをテスト"""
    mock_llm_client.generate.return_value = "回答"

    task = Task.create_general_answer("タスク")
    multiline_result = """これは
複数行の
タスク結果です"""
    task.complete(multiline_result)
    task_plan = TaskPlan.create(message_id=uuid4(), tasks=[task])

    result = await answer_service.execute(chat_session_with_messages, task_plan)

    # マルチラインの結果が含まれていることを確認
    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]
    last_message = messages[-1]
    assert multiline_result in last_message.content


@pytest.mark.asyncio
async def test_execute_with_long_conversation_history(
    answer_service, mock_llm_client
):
    """長い会話履歴がある場合のテスト"""
    mock_llm_client.generate.return_value = "回答"

    session = ChatSession.create(
        id="session-1", thread_id="thread-1", user_id="U12345", channel_id="C12345"
    )

    # 長い会話履歴を作成
    for i in range(10):
        session.add_user_message(f"質問{i}")
        session.add_assistant_message(f"回答{i}")

    task = Task.create_general_answer("タスク")
    task.complete("結果")
    task_plan = TaskPlan.create(message_id=uuid4(), tasks=[task])

    result = await answer_service.execute(session, task_plan)

    # 会話履歴が適切に含まれることを確認
    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # システムプロンプト(1) + 会話履歴(19個、最新の1個を除く) + 新しいプロンプト(1) = 21
    assert len(messages) == 21