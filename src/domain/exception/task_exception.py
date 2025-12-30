from src.domain.exception.base import DomainException


class TaskException(DomainException):
    pass


class EmptyTaskDescriptionError(TaskException):
    """タスクの説明が空の場合の例外"""

    status_code = 422  # Unprocessable Entity

    def __init__(self, message: str = "タスクの説明が空です。"):
        super().__init__(message)


class MissingTaskLogError(TaskException):
    """タスクログが必要な場合の例外"""

    status_code = 422  # Unprocessable Entity

    def __init__(self, message: str = "タスクログが必要です。"):
        super().__init__(message)


class InvalidTaskStatusError(TaskException):
    """タスクの状態が不正な場合の例外"""

    status_code = 422

    def __init__(self, message: str):
        super().__init__(message)


class TaskNotInProgressError(InvalidTaskStatusError):
    """実行中でないタスクを完了しようとした場合の例外"""

    def __init__(self, current_status: str):
        message = f"実行中でないタスクは完了できません: {current_status}"
        super().__init__(message)


class TaskNotCompletedError(InvalidTaskStatusError):
    """完了していないタスクの結果を更新しようとした場合の例外"""

    def __init__(self, current_status: str):
        message = f"完了していないタスクの結果は更新できません: {current_status}"
        super().__init__(message)
