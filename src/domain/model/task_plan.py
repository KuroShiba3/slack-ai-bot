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

    def format_task_results(self) -> str:
        """タスク結果のフォーマット"""
        task_results_parts = []
        for task in self._tasks:
            if task.result:
                task_results_parts.append(
                    f"## タスク: {task.description}\n\n{task.result}"
                )
        return "\n\n---\n\n".join(task_results_parts)
