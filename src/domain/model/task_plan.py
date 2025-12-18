from uuid import UUID, uuid4

from .task import Task, TaskStatus


class TaskPlan:
    def __init__(
        self,
        id: UUID,
        message_id: UUID,
        tasks: list[Task],
    ):
        if not tasks:
            raise ValueError("タスクが空です。")

        self._id = id
        self._message_id = message_id
        self._tasks = tasks

    @classmethod
    def create(cls, message_id: UUID, tasks: list[Task]) -> "TaskPlan":
        return cls(
            id=uuid4(),
            message_id=message_id,
            tasks=tasks
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def message_id(self) -> UUID:
        return self._message_id

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    def get_incomplete_tasks(self) -> list[Task]:
        """未完了のタスクを取得"""
        return [
            task for task in self._tasks
            if task.status != TaskStatus.COMPLETED
        ]

    def get_completed_tasks(self) -> list[Task]:
        """完了済みタスクを取得"""
        return [
            task for task in self._tasks
            if task.status == TaskStatus.COMPLETED
        ]

    def is_all_tasks_completed(self) -> bool:
        """すべてのタスクが完了したか確認"""
        return all(
            task.status == TaskStatus.COMPLETED
            for task in self._tasks
        )

    def get_task_results(self) -> list[str]:
        """完了したタスクの結果を取得"""
        results = []
        for task in self.get_completed_tasks():
            if task.result:
                results.append(task.result)
        return results
