from src.domain.exception.base import DomainException


class TaskLogException(DomainException):
    pass


class EmptyResponseError(TaskLogException):
    """生成レスポンスが空の場合の例外"""

    status_code = 422  # Unprocessable Entity

    def __init__(self, message: str = "生成レスポンスが空です"):
        super().__init__(message)


class EmptySearchQueryError(TaskLogException):
    """検索クエリが空の場合の例外"""

    status_code = 422

    def __init__(self, message: str = "検索クエリが空です"):
        super().__init__(message)


class InvalidSearchResultsError(TaskLogException):
    """検索結果がNoneの場合の例外"""

    status_code = 422

    def __init__(self, message: str = "検索結果がNoneです"):
        super().__init__(message)
