from typing import Optional
from ...domain.model.task import Task
from ...log import get_logger
from ...domain.model import WebSearchTaskLog, GeneralAnswerTaskLog

logger = get_logger(__name__)


class TaskStateService:

    @staticmethod
    def get_task_by_id(state: dict, task_id: str) -> Optional[Task]:
        tasks = state.get("tasks", [])
        for task_dict in tasks:
            if task_dict.get("id") == task_id:
                return Task.from_dict(task_dict)
        return None

    @staticmethod
    def add_web_search_attempt(state: dict, task_id: str, query: str, results: list) -> dict:

        tasks = state.get("tasks", [])
        updated_tasks = []

        for task_dict in tasks:
            if task_dict.get("id") == task_id:
                task = Task.from_dict(task_dict)
                if not task.log:
                    task.log = WebSearchTaskLog()
                if isinstance(task.log, WebSearchTaskLog):
                    task.log.add_attempt(query, results)
                updated_tasks.append(task.to_dict())
            else:
                updated_tasks.append(task_dict)

        return {"tasks": updated_tasks}

    @staticmethod
    def add_general_answer_attempt(state: dict, task_id: str, prompt: str, response: str) -> dict:

        tasks = state.get("tasks", [])
        updated_tasks = []

        for task_dict in tasks:
            if task_dict.get("id") == task_id:
                task = Task.from_dict(task_dict)
                if not task.log:
                    task.log = GeneralAnswerTaskLog()
                if isinstance(task.log, GeneralAnswerTaskLog):
                    task.log.add_attempt(prompt, response)
                updated_tasks.append(task.to_dict())
            else:
                updated_tasks.append(task_dict)

        return {"tasks": updated_tasks}

    @staticmethod
    def complete_task(state: dict, task_id: str, result: str) -> dict:
        """タスクを完了状態に更新"""
        tasks = state.get("tasks", [])
        updated_tasks = []

        for task_dict in tasks:
            if task_dict.get("id") == task_id:
                task = Task.from_dict(task_dict)
                task.complete(result)
                updated_tasks.append(task.to_dict())
            else:
                updated_tasks.append(task_dict)

        return {"tasks": updated_tasks}

    @staticmethod
    def get_task_results_text(state: dict) -> str:
        tasks = state.get("tasks", [])
        results = []

        for i, task_dict in enumerate(tasks, 1):
            task = Task.from_dict(task_dict)
            if task.is_completed():
                results.append(f"### タスク{i}: {task.description}")
                results.append(f"{task.result or 'No result'}")
                results.append("")

        if not results:
            return ""

        return "\n".join(results)