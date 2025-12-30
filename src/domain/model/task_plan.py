from uuid import UUID, uuid4

from src.domain.exception.task_plan_exception import (
    AllTasksFailedError,
    EmptyTaskListError,
)

from .task import Task, TaskStatus


class TaskPlan:
    def __init__(
        self,
        id: UUID,
        message_id: UUID,
        tasks: list[Task],
    ):
        if not tasks:
            raise EmptyTaskListError()

        self._id = id
        self._message_id = message_id
        self._tasks = tasks

    @classmethod
    def create(cls, message_id: UUID, tasks: list[Task]) -> "TaskPlan":
        return cls(id=uuid4(), message_id=message_id, tasks=tasks)

    @classmethod
    def reconstruct(cls, id: UUID, message_id: UUID, tasks: list[Task]) -> "TaskPlan":
        return cls(id=id, message_id=message_id, tasks=tasks)

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
        """タスク結果のフォーマット (完了したタスクのみ)"""
        task_results_parts = []
        for i, task in enumerate(self._tasks, 1):
            if task.status == TaskStatus.COMPLETED:
                task_results_parts.append(
                    f"## タスク {i}: {task.description}\n\n"
                    f"### エージェント\n{task.agent_name.value}\n\n"
                    f"### 結果\n{task.result}"
                )

        if not task_results_parts:
            raise AllTasksFailedError()

        formatted_results = "\n\n---\n\n".join(task_results_parts)
        return f"# タスク実行結果サマリー\n\n実行済みタスク数: {len(task_results_parts)}/{len(self._tasks)}\n\n---\n\n{formatted_results}"
