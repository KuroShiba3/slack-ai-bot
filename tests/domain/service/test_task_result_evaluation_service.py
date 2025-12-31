from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from src.domain.exception.service_exception import TaskResultNotFoundError
from src.domain.model import SearchResult
from src.domain.model.task import Task
from src.domain.model.task_evaluation import TaskEvaluation
from src.domain.service.task_result_evaluation_service import (
    TaskResultEvaluationService,
)


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def evaluation_service(mock_llm_client):
    """TaskResultEvaluationServiceのインスタンス"""
    return TaskResultEvaluationService(llm_client=mock_llm_client)


@pytest.fixture
def completed_task():
    """完了したタスク"""
    task = Task.create_web_search("Pythonの最新バージョンを検索")
    task.complete("Python 3.13がリリースされました")
    return task


@pytest.fixture
def task_with_search_results():
    """検索結果を持つタスク"""
    task = Task.create_web_search("Pythonの最新バージョンを検索")

    # 検索結果を追加
    search_results = [
        SearchResult(
            title="Python 3.13 Released",
            url="https://www.python.org/downloads/release/python-3130/",
            content="Python 3.13.0 is now available",
        ),
        SearchResult(
            title="What's New in Python 3.13",
            url="https://docs.python.org/3.13/whatsnew/3.13.html",
            content="New features and improvements",
        ),
    ]

    task.task_log.add_attempt(
        query="Python 3.13 release",
        results=search_results,
    )
    task.complete("Python 3.13が2024年にリリースされました")

    return task


@pytest.mark.asyncio
async def test_execute_evaluates_task_result(
    evaluation_service, mock_llm_client, completed_task
):
    """タスク結果を評価するテスト"""
    mock_evaluation = TaskEvaluation(
        is_satisfactory=True,
        need=None,
        reason="タスク結果は十分です",
        feedback=None,
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    result = await evaluation_service.execute(completed_task)

    assert result.is_satisfactory is True
    assert result.need is None
    assert result.reason == "タスク結果は十分です"
    assert mock_llm_client.generate_with_structured_output.called


@pytest.mark.asyncio
async def test_execute_with_unsatisfactory_result(
    evaluation_service, mock_llm_client, completed_task
):
    """不十分なタスク結果の評価テスト"""
    mock_evaluation = TaskEvaluation(
        is_satisfactory=False,
        need="search",
        reason="検索結果が不十分です",
        feedback="より具体的な検索クエリを使用してください",
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    result = await evaluation_service.execute(completed_task)

    assert result.is_satisfactory is False
    assert result.need == "search"
    assert result.feedback == "より具体的な検索クエリを使用してください"


@pytest.mark.asyncio
async def test_execute_raises_error_when_no_result(evaluation_service):
    """タスク結果がない場合にエラーを投げるテスト"""
    task = Task.create_web_search("タスク")
    # task.complete()を呼ばない（結果なし）

    with pytest.raises(TaskResultNotFoundError):
        await evaluation_service.execute(task)


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    evaluation_service, mock_llm_client, completed_task
):
    """システムプロンプトが含まれることをテスト"""
    mock_evaluation = TaskEvaluation(
        is_satisfactory=True,
        need=None,
        reason="テスト",
        feedback=None,
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    await evaluation_service.execute(completed_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "タスク結果品質を評価する専門家" in messages[0].content


@pytest.mark.asyncio
async def test_execute_includes_task_description_and_result(
    evaluation_service, mock_llm_client, completed_task
):
    """タスクの説明と結果が含まれることをテスト"""
    mock_evaluation = TaskEvaluation(
        is_satisfactory=True,
        need=None,
        reason="テスト",
        feedback=None,
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    await evaluation_service.execute(completed_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "Pythonの最新バージョンを検索" in user_message.content
    assert "Python 3.13がリリースされました" in user_message.content


@pytest.mark.asyncio
async def test_execute_includes_search_results(
    evaluation_service, mock_llm_client, task_with_search_results
):
    """検索結果が含まれることをテスト"""
    mock_evaluation = TaskEvaluation(
        is_satisfactory=True,
        need=None,
        reason="テスト",
        feedback=None,
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    await evaluation_service.execute(task_with_search_results)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    user_message = messages[-1]
    assert "取得した検索結果" in user_message.content
    assert "Python 3.13 Released" in user_message.content
    assert (
        "https://www.python.org/downloads/release/python-3130/" in user_message.content
    )


@pytest.mark.asyncio
async def test_get_search_results_from_task(
    evaluation_service, task_with_search_results
):
    """タスクログから検索結果を取得するテスト"""
    results = evaluation_service._get_search_results_from_task(task_with_search_results)

    assert len(results) == 2
    assert results[0].title == "Python 3.13 Released"
    assert results[1].title == "What's New in Python 3.13"


@pytest.mark.asyncio
async def test_get_search_results_from_task_without_results(evaluation_service):
    """検索結果がないタスクのテスト"""
    task = Task.create_general_answer("一般回答タスク")
    task.complete("回答")

    results = evaluation_service._get_search_results_from_task(task)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_build_human_prompt_format(evaluation_service):
    """_build_human_promptが正しいフォーマットを生成することをテスト"""
    task_description = "Pythonについて調べる"
    task_result = "Pythonはプログラミング言語です"
    search_results = [
        SearchResult(
            title="Python公式サイト",
            url="https://www.python.org/",
            content="Python is a programming language",
        )
    ]

    prompt = evaluation_service._build_human_prompt(
        task_description=task_description,
        task_result=task_result,
        search_results=search_results,
    )

    assert "## 現在の日付:" in prompt
    assert "## 割り当てられたタスク:" in prompt
    assert task_description in prompt
    assert "## 生成されたタスク結果:" in prompt
    assert task_result in prompt
    assert "## 取得した検索結果:" in prompt
    assert "Python公式サイト" in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_without_search_results(evaluation_service):
    """検索結果がない場合のプロンプト生成テスト"""
    task_description = "タスク"
    task_result = "結果"
    search_results = []

    prompt = evaluation_service._build_human_prompt(
        task_description=task_description,
        task_result=task_result,
        search_results=search_results,
    )

    assert "## 現在の日付:" in prompt
    assert "## 割り当てられたタスク:" in prompt
    assert "## 生成されたタスク結果:" in prompt
    assert "## 取得した検索結果:" not in prompt


@pytest.mark.asyncio
async def test_execute_with_need_generate(evaluation_service, mock_llm_client):
    """タスク結果改善が必要な場合のテスト"""
    task = Task.create_web_search("タスク")
    task.complete("不完全な結果")

    mock_evaluation = TaskEvaluation(
        is_satisfactory=False,
        need="generate",
        reason="検索結果の重要情報が活用されていない",
        feedback="検索結果の具体的な数値を含めてください",
    )

    mock_llm_client.generate_with_structured_output.return_value = mock_evaluation

    result = await evaluation_service.execute(task)

    assert result.is_satisfactory is False
    assert result.need == "generate"
    assert "検索結果の重要情報" in result.reason
