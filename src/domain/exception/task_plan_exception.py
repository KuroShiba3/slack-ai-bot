from src.domain.exception.base import DomainException


class TaskPlanException(DomainException):
    pass


class EmptyTaskListError(TaskPlanException):
    """タスクリストが空の場合の例外"""

    status_code = 422

    def __init__(self, message: str = "タスクが空です。"):
        super().__init__(message)


class AllTasksFailedError(TaskPlanException):
    """全てのタスクが失敗した場合の例外"""

    status_code = 422

    def __init__(self, message: str = "全てのタスクが失敗しました。"):
        super().__init__(message)
