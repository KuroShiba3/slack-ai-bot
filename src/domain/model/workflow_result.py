from dataclasses import dataclass

from .task_plan import TaskPlan


@dataclass(frozen=True)
class WorkflowResult:
    answer: str
    task_plan: TaskPlan
