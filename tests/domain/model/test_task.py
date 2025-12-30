from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.domain.exception.task_exception import (
    EmptyTaskDescriptionError,
    TaskNotCompletedError,
    TaskNotInProgressError,
)
from src.domain.model.general_answer_task_log import GeneralAnswerTaskLog
from src.domain.model.task import AgentName, Task, TaskStatus
from src.domain.model.web_search_task_log import SearchResult, WebSearchTaskLog


def test_create_web_search_task():
    """Web検索タスクの生成テスト"""
    description = "Pythonの最新情報を検索"
    task = Task.create_web_search(description)

    assert task.description == description
    assert task.agent_name == AgentName.WEB_SEARCH
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.result is None
    assert isinstance(task.id, UUID)
    assert isinstance(task.created_at, datetime)
    assert task.completed_at is None
    assert isinstance(task.task_log, WebSearchTaskLog)


def test_create_general_answer_task():
    """一般回答タスクの生成テスト"""
    description = "Pythonの特徴を説明"
    task = Task.create_general_answer(description)

    assert task.description == description
    assert task.agent_name == AgentName.GENERAL_ANSWER
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.result is None
    assert isinstance(task.id, UUID)
    assert isinstance(task.created_at, datetime)
    assert task.completed_at is None
    assert isinstance(task.task_log, GeneralAnswerTaskLog)


def test_add_web_search_attempt_success():
    """Web検索タスクに試行を追加する成功テスト"""
    task = Task.create_web_search("検索タスク")
    query = "Python tutorial"
    results = [
        SearchResult(
            url="https://example.com",
            title="Python入門",
            content="Pythonの基本",
        )
    ]

    task.add_web_search_attempt(query=query, results=results)

    assert isinstance(task.task_log, WebSearchTaskLog)
    assert len(task.task_log.attempts) == 1
    assert task.task_log.attempts[0].query == query
    assert task.task_log.attempts[0].results == results


def test_add_web_search_attempt_to_general_answer_task_raises_error():
    """一般回答タスクにWeb検索試行を追加するとエラーになるテスト"""
    task = Task.create_general_answer("一般回答タスク")
    query = "Python"
    results = [
        SearchResult(url="https://example.com", title="Title", content="Content")
    ]

    with pytest.raises(TypeError, match="このタスクはWeb検索タスクではありません"):
        task.add_web_search_attempt(query=query, results=results)


def test_add_general_answer_attempt_success():
    """一般回答タスクに試行を追加する成功テスト"""
    task = Task.create_general_answer("一般回答タスク")
    response = "これはPythonに関する回答です"

    task.add_general_answer_attempt(response=response)

    assert isinstance(task.task_log, GeneralAnswerTaskLog)
    assert len(task.task_log.attempts) == 1
    assert task.task_log.attempts[0].response == response


def test_add_general_answer_attempt_to_web_search_task_raises_error():
    """Web検索タスクに一般回答試行を追加するとエラーになるテスト"""
    task = Task.create_web_search("Web検索タスク")
    response = "これは回答です"

    with pytest.raises(TypeError, match="このタスクは一般回答タスクではありません"):
        task.add_general_answer_attempt(response=response)


def test_complete_task():
    """タスクを完了するテスト"""
    task = Task.create_web_search("検索タスク")
    result = "検索結果をまとめました"

    task.complete(result)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == result
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)


def test_complete_task_with_empty_result():
    """空の結果でタスクを完了するとFailedになるテスト"""
    task = Task.create_web_search("検索タスク")

    task.complete("")

    assert task.status == TaskStatus.FAILED
    assert task.result == "Error: タスク実行結果が空でした"


def test_complete_already_completed_task_raises_error():
    """既に完了したタスクを再度完了しようとするとエラーになるテスト"""
    task = Task.create_web_search("検索タスク")
    task.complete("結果")

    with pytest.raises(TaskNotInProgressError, match="実行中でないタスクは完了できません"):
        task.complete("別の結果")


def test_complete_failed_task_raises_error():
    """失敗したタスクを完了しようとするとエラーになるテスト"""
    task = Task.create_web_search("検索タスク")
    task.fail("エラーが発生")

    with pytest.raises(TaskNotInProgressError, match="実行中でないタスクは完了できません"):
        task.complete("結果")


def test_update_result():
    """タスク結果を更新するテスト"""
    task = Task.create_web_search("検索タスク")
    task.complete("最初の結果")

    new_result = "更新された結果"
    task.update_result(new_result)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == new_result


def test_update_result_on_in_progress_task_raises_error():
    """実行中のタスクの結果を更新しようとするとエラーになるテスト"""
    task = Task.create_web_search("検索タスク")

    with pytest.raises(TaskNotCompletedError, match="完了していないタスクの結果は更新できません"):
        task.update_result("新しい結果")


def test_update_result_with_empty_string():
    """空文字列で結果を更新するとFailedになるテスト"""
    task = Task.create_web_search("検索タスク")
    task.complete("最初の結果")

    task.update_result("")

    assert task.status == TaskStatus.FAILED
    assert task.result == "Error: タスク実行結果が空でした"


def test_fail_task():
    """タスクを失敗させるテスト"""
    task = Task.create_web_search("検索タスク")
    error_message = "APIエラーが発生しました"

    task.fail(error_message)

    assert task.status == TaskStatus.FAILED
    assert task.result == f"Error: {error_message}"
    assert task.completed_at is not None


def test_reconstruct_task():
    """タスクを再構築するテスト"""
    task_id = uuid4()
    description = "再構築されたタスク"
    agent_name = AgentName.WEB_SEARCH
    task_log = WebSearchTaskLog.create()
    status = TaskStatus.COMPLETED
    result = "完了結果"
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    completed_at = datetime(2024, 1, 1, 13, 0, 0)

    task = Task.reconstruct(
        id=task_id,
        description=description,
        agent_name=agent_name,
        task_log=task_log,
        status=status,
        result=result,
        created_at=created_at,
        completed_at=completed_at,
    )

    assert task.id == task_id
    assert task.description == description
    assert task.agent_name == agent_name
    assert task.task_log == task_log
    assert task.status == status
    assert task.result == result
    assert task.created_at == created_at
    assert task.completed_at == completed_at


def test_create_task_with_empty_description_raises_error():
    """空の説明でタスクを作成するとエラーになるテスト"""
    with pytest.raises(EmptyTaskDescriptionError, match="タスクの説明が空です"):
        Task(
            id=uuid4(),
            description="",
            agent_name=AgentName.WEB_SEARCH,
            task_log=WebSearchTaskLog.create(),
        )


def test_task_id_is_unique():
    """生成されるタスクIDがユニークであることをテスト"""
    task1 = Task.create_web_search("タスク1")
    task2 = Task.create_web_search("タスク2")

    assert task1.id != task2.id


def test_multiple_web_search_attempts():
    """複数のWeb検索試行を追加するテスト"""
    task = Task.create_web_search("検索タスク")

    for i in range(3):
        query = f"query{i}"
        results = [
            SearchResult(
                url=f"https://example.com/{i}",
                title=f"Title{i}",
                content=f"Content{i}",
            )
        ]
        task.add_web_search_attempt(query=query, results=results)

    assert isinstance(task.task_log, WebSearchTaskLog)
    assert len(task.task_log.attempts) == 3
