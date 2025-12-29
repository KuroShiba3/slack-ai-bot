from uuid import UUID, uuid4

import pytest

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

    with pytest.raises(ValueError, match="タスクが空です"):
        TaskPlan.create(message_id=message_id, tasks=[])


def test_task_plan_id_is_unique():
    """生成されるタスク計画IDがユニークであることをテスト"""
    message_id = uuid4()
    tasks = [Task.create_web_search("検索タスク")]

    task_plan1 = TaskPlan.create(message_id=message_id, tasks=tasks)
    task_plan2 = TaskPlan.create(message_id=message_id, tasks=tasks)

    assert task_plan1.id != task_plan2.id


def test_format_task_results_with_no_completed_tasks():
    """完了したタスクがない場合のフォーマットテスト"""
    message_id = uuid4()
    tasks = [
        Task.create_web_search("検索タスク1"),
        Task.create_general_answer("一般回答タスク1"),
    ]
    task_plan = TaskPlan.create(message_id=message_id, tasks=tasks)

    result = task_plan.format_task_results()

    assert "完了したタスクがありません" in result


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
    assert "ステータス" in result
    assert "completed" in result
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
