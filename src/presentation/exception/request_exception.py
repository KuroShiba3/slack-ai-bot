from src.presentation.exception.base import PresentationException


class RequestException(PresentationException):
    pass


class InvalidRequestError(RequestException):
    """リクエストデータが不正な場合の例外"""

    status_code = 400

    def __init__(self, field_name: str):
        self.field_name = field_name
        message = f"{field_name}が不正です"
        super().__init__(message)
