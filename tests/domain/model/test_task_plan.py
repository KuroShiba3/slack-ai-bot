from uuid import UUID, uuid4

import pytest

from src.domain.exception.task_plan_exception import (
    AllTasksFailedError,
    EmptyTaskListError,
)
from src.domain.model.task import Task
from src.domain.model.task_plan import TaskPlan


def test_create_task_plan():
    """タスク計画を生成するテスト"""
    message_id = uuid4()
    tasks = [
        Task.create_web_search("Web検索タスク"),
        Task.create_general_answer("一般回答タスク"),
    ]

    task_plan = TaskPlan.create(message_id=message_id, tasks=tasks)

    assert isinstance(task_plan.id, UUID)
    assert task_plan.message_id == message_id
    assert task_plan.tasks == tasks
    assert len(task_plan.tasks) == 2


def test_create_task_plan_with_empty_tasks_raises_error():
    """空のタスクリストでタスク計画を作成するとエラーになるテスト"""
    message_id = uuid4()

    with pytest.raises(EmptyTaskListError, match="タスクが空です"):
        TaskPlan.create(message_id=message_id, tasks=[])


def test_task_plan_id_is_unique():
    """生成されるタスク計画IDがユニークであることをテスト"""
    message_id = uuid4()
    tasks = [Task.create_web_search("検索タスク")]

    task_plan1 = TaskPlan.create(message_id=message_id, tasks=tasks)
    task_plan2 = TaskPlan.create(message_id=message_id, tasks=tasks)

    assert task_plan1.id != task_plan2.id


def test_format_task_results_with_no_completed_tasks():
    """完了したタスクがない場合は例外が発生するテスト"""
    message_id = uuid4()
    tasks = [
        Task.create_web_search("検索タスク1"),
        Task.create_general_answer("一般回答タスク1"),
    ]
    task_plan = TaskPlan.create(message_id=message_id, tasks=tasks)

    with pytest.raises(AllTasksFailedError, match="全てのタスクが失敗しました"):
        task_plan.format_task_results()


def test_format_task_results_with_single_completed_task():
    """単一の完了タスクのフォーマットテスト"""
    message_id = uuid4()
    task = Task.create_web_search("Pythonの最新情報を検索")
    task.complete("Python 3.13がリリースされました")

    task_plan = TaskPlan.create(message_id=message_id, tasks=[task])

    result = task_plan.format_task_results()

    assert "タスク実行結果サマリー" in result
    assert "実行済みタスク数: 1/1" in result
    assert "タスク 1: Pythonの最新情報を検索" in result
    assert "エージェント" in result
    assert "web_search" in result
    assert "結果" in result
    assert "Python 3.13がリリースされました" in result


def test_format_task_results_with_multiple_completed_tasks():
    """複数の完了タスクのフォーマットテスト"""
    message_id = uuid4()

    task1 = Task.create_web_search("検索タスク1")
    task1.complete("検索結果1")

    task2 = Task.create_general_answer("一般回答タスク1")
    task2.complete("回答結果1")

    task_plan = TaskPlan.create(message_id=message_id, tasks=[task1, task2])

    result = task_plan.format_task_results()

    assert "実行済みタスク数: 2/2" in result
    assert "タスク 1: 検索タスク1" in result
    assert "タスク 2: 一般回答タスク1" in result
    assert "検索結果1" in result
    assert "回答結果1" in result


def test_format_task_results_with_failed_tasks():
    """失敗したタスクが含まれる場合は除外されるテスト"""
    message_id = uuid4()

    task1 = Task.create_web_search("検索タスク1")
    task1.complete("検索結果1")

    task2 = Task.create_general_answer("一般回答タスク2")
    task2.fail("エラーが発生しました")

    task_plan = TaskPlan.create(message_id=message_id, tasks=[task1, task2])

    result = task_plan.format_task_results()

    # 完了したタスクのみ含まれる
    assert "実行済みタスク数: 1/2" in result
    assert "検索結果1" in result
    # 失敗したタスクのエラーメッセージは含まれない
    assert "Error:" not in result
    assert "エラーが発生しました" not in result


def test_format_task_results_with_all_failed_tasks():
    """全てのタスクが失敗した場合は例外が発生するテスト"""
    message_id = uuid4()

    task1 = Task.create_web_search("検索タスク1")
    task1.fail("検索に失敗")

    task2 = Task.create_general_answer("一般回答タスク2")
    task2.fail("回答生成に失敗")

    task_plan = TaskPlan.create(message_id=message_id, tasks=[task1, task2])

    with pytest.raises(AllTasksFailedError, match="全てのタスクが失敗しました"):
        task_plan.format_task_results()
