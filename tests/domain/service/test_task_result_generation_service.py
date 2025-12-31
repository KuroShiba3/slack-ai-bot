from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.domain.model import SearchResult
from src.domain.model.task import Task, TaskStatus
from src.domain.service.task_result_generation_service import (
    TaskResultGenerationService,
)


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def task_result_service(mock_llm_client):
    """TaskResultGenerationServiceのインスタンス"""
    return TaskResultGenerationService(llm_client=mock_llm_client)


@pytest.fixture
def task_with_search_results():
    """検索結果を持つタスク"""
    task = Task.create_web_search("Pythonの最新バージョンを検索")

    # 検索結果を追加
    search_results = [
        SearchResult(
            title="Python 3.13 Released",
            url="https://www.python.org/downloads/release/python-3130/",
            content="Python 3.13.0 is now available. This release includes...",
        ),
        SearchResult(
            title="What's New in Python 3.13",
            url="https://docs.python.org/3.13/whatsnew/3.13.html",
            content="New features: improved performance, better error messages...",
        ),
    ]

    task.task_log.add_attempt(
        query="Python 3.13 release",
        results=search_results,
    )

    return task


@pytest.mark.asyncio
async def test_execute_generates_task_result(
    task_result_service, mock_llm_client, task_with_search_results
):
    """検索結果からタスク結果を生成するテスト"""
    mock_llm_client.generate.return_value = "Python 3.13が2024年にリリースされました[0]\n\n【参考情報】(1件)\n[0] <https://www.python.org/downloads/release/python-3130/|Python 3.13 Released>"

    await task_result_service.execute(task_with_search_results)

    assert mock_llm_client.generate.called
    assert task_with_search_results.status == TaskStatus.COMPLETED
    assert "Python 3.13" in task_with_search_results.result


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    task_result_service, mock_llm_client, task_with_search_results
):
    """システムプロンプトが含まれることをテスト"""
    mock_llm_client.generate.return_value = "タスク結果"

    await task_result_service.execute(task_with_search_results)

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "タスク実行エージェント" in messages[0].content
    assert (
        "Slack mrkdwn形式" in messages[0].content
        or "Slackリンク形式" in messages[0].content
    )


@pytest.mark.asyncio
async def test_execute_includes_task_description(
    task_result_service, mock_llm_client, task_with_search_results
):
    """タスクの説明が含まれることをテスト"""
    mock_llm_client.generate.return_value = "タスク結果"

    await task_result_service.execute(task_with_search_results)

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "Pythonの最新バージョンを検索" in user_message.content


@pytest.mark.asyncio
async def test_execute_includes_search_results(
    task_result_service, mock_llm_client, task_with_search_results
):
    """検索結果が含まれることをテスト"""
    mock_llm_client.generate.return_value = "タスク結果"

    await task_result_service.execute(task_with_search_results)

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "取得した検索結果" in user_message.content
    assert "Python 3.13 Released" in user_message.content
    assert (
        "https://www.python.org/downloads/release/python-3130/" in user_message.content
    )
    assert "Python 3.13.0 is now available" in user_message.content


@pytest.mark.asyncio
async def test_execute_with_feedback(
    task_result_service, mock_llm_client, task_with_search_results
):
    """フィードバック付きでタスク結果を生成するテスト"""
    mock_llm_client.generate.return_value = "改善されたタスク結果"

    feedback = "より具体的な日付を含めてください"
    previous_result = "Python 3.13がリリースされました"

    await task_result_service.execute(
        task_with_search_results,
        feedback=feedback,
        previous_result=previous_result,
    )

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "改善フィードバック" in user_message.content
    assert feedback in user_message.content
    assert "以前のタスク結果" in user_message.content
    assert previous_result in user_message.content


@pytest.mark.asyncio
async def test_execute_updates_result_when_already_completed(
    task_result_service, mock_llm_client, task_with_search_results
):
    """既に完了しているタスクの結果を更新するテスト"""
    # タスクを一度完了させる
    task_with_search_results.complete("古い結果")

    mock_llm_client.generate.return_value = "新しい結果"

    await task_result_service.execute(task_with_search_results)

    assert task_with_search_results.status == TaskStatus.COMPLETED
    assert task_with_search_results.result == "新しい結果"


@pytest.mark.asyncio
async def test_get_search_results_from_task(
    task_result_service, task_with_search_results
):
    """タスクログから検索結果を取得するテスト"""
    results = task_result_service._get_search_results_from_task(
        task_with_search_results
    )

    assert len(results) == 2
    assert results[0].title == "Python 3.13 Released"
    assert results[1].title == "What's New in Python 3.13"


@pytest.mark.asyncio
async def test_get_search_results_from_task_with_multiple_attempts(
    task_result_service,
):
    """複数の検索試行がある場合のテスト"""
    task = Task.create_web_search("タスク")

    # 1回目の検索試行
    task.task_log.add_attempt(
        query="query1",
        results=[
            SearchResult(
                title="Result 1",
                url="https://example.com/1",
                content="Content 1",
            )
        ],
    )

    # 2回目の検索試行
    task.task_log.add_attempt(
        query="query2",
        results=[
            SearchResult(
                title="Result 2",
                url="https://example.com/2",
                content="Content 2",
            )
        ],
    )

    results = task_result_service._get_search_results_from_task(task)

    # 両方の試行の結果が含まれることを確認
    assert len(results) == 2
    assert results[0].title == "Result 1"
    assert results[1].title == "Result 2"


@pytest.mark.asyncio
async def test_build_human_prompt_format(task_result_service):
    """_build_human_promptが正しいフォーマットを生成することをテスト"""
    task_description = "Pythonについて調べる"
    search_results = [
        SearchResult(
            title="Python公式サイト",
            url="https://www.python.org/",
            content="Python is a programming language",
        )
    ]

    prompt = task_result_service._build_human_prompt(
        task_description=task_description,
        search_results=search_results,
        feedback=None,
        previous_result=None,
    )

    assert "## 現在の日付:" in prompt
    assert "## 割り当てられたタスク:" in prompt
    assert task_description in prompt
    assert "## 取得した検索結果:" in prompt
    assert "Python公式サイト" in prompt
    assert "https://www.python.org/" in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_without_feedback(task_result_service):
    """フィードバックなしのプロンプト生成テスト"""
    task_description = "タスク"
    search_results = []

    prompt = task_result_service._build_human_prompt(
        task_description=task_description,
        search_results=search_results,
        feedback=None,
        previous_result=None,
    )

    assert "## 改善フィードバック" not in prompt
    assert "## 以前のタスク結果" not in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_with_feedback_and_previous_result(
    task_result_service,
):
    """フィードバックと以前の結果を含むプロンプト生成テスト"""
    task_description = "タスク"
    search_results = []
    feedback = "改善が必要"
    previous_result = "以前の結果"

    prompt = task_result_service._build_human_prompt(
        task_description=task_description,
        search_results=search_results,
        feedback=feedback,
        previous_result=previous_result,
    )

    assert "## 改善フィードバック:" in prompt
    assert feedback in prompt
    assert "## 以前のタスク結果:" in prompt
    assert previous_result in prompt
    assert "フィードバックを参考にして" in prompt


@pytest.mark.asyncio
async def test_execute_completes_in_progress_task(task_result_service, mock_llm_client):
    """IN_PROGRESSのタスクを完了させるテスト"""
    task = Task.create_web_search("タスク")

    # 検索結果を追加
    task.task_log.add_attempt(
        query="query",
        results=[
            SearchResult(
                title="Result",
                url="https://example.com/",
                content="Content",
            )
        ],
    )

    mock_llm_client.generate.return_value = "タスク結果"

    await task_result_service.execute(task)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == "タスク結果"


@pytest.mark.asyncio
async def test_execute_with_empty_search_results(task_result_service, mock_llm_client):
    """検索結果が空の場合のテスト"""
    task = Task.create_web_search("タスク")

    mock_llm_client.generate.return_value = "検索結果がありませんでした"

    await task_result_service.execute(task)

    call_args = mock_llm_client.generate.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "## 取得した検索結果:" not in user_message.content
    assert task.status == TaskStatus.COMPLETED
