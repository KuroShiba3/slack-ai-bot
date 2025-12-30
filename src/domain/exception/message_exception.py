from src.domain.exception.base import DomainException


class MessageException(DomainException):
    pass


class EmptyMessageContentError(MessageException):
    """メッセージの内容が空の場合の例外"""

    status_code = 422

    def __init__(self, message: str = "メッセージの内容が空です。"):
        super().__init__(message)
