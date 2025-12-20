from dataclasses import dataclass

from .task_plan import TaskPlan


@dataclass(frozen=True)
class WorkflowResult:
    """ワークフロー実行結果を表す値オブジェクト"""
    answer: str
    task_plan: TaskPlan
