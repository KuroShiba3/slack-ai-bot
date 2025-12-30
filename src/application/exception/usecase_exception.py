from src.application.exception.base import ApplicationException


class UseCaseException(ApplicationException):
    pass


class InvalidInputError(UseCaseException):
    """入力データが不正な場合の例外"""

    status_code = 422

    def __init__(self, field_name: str):
        self.field_name = field_name
        message = f"{field_name}が不正です"
        super().__init__(message)
