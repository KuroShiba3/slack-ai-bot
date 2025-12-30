from src.domain.exception.base import DomainException


class ChatSessionException(DomainException):
    pass


class InvalidMessageRoleError(ChatSessionException):
    """メッセージの役割が不正な場合の例外"""

    status_code = 422

    def __init__(self, message: str):
        super().__init__(message)


class InvalidUserMessageRoleError(InvalidMessageRoleError):
    """USERロール以外のメッセージを追加しようとした場合の例外"""

    def __init__(self):
        message = "USER以外のメッセージは追加できません"
        super().__init__(message)


class InvalidAssistantMessageRoleError(InvalidMessageRoleError):
    """ASSISTANTロール以外のメッセージを追加しようとした場合の例外"""

    def __init__(self):
        message = "ASSISTANT以外のメッセージは追加できません"
        super().__init__(message)


class NoneTaskPlanError(ChatSessionException):
    """Noneのタスク計画を追加しようとした場合の例外"""

    status_code = 422

    def __init__(self, message: str = "タスク計画がNoneです"):
        super().__init__(message)


class UserMessageNotFoundError(ChatSessionException):
    """ユーザーメッセージが存在しない場合の例外"""

    status_code = 404

    def __init__(self, message: str = "ユーザーメッセージが存在しません"):
        super().__init__(message)


class AssistantMessageNotFoundError(ChatSessionException):
    """アシスタントメッセージが存在しない場合の例外"""

    status_code = 404

    def __init__(self, message: str = "アシスタントメッセージが存在しません"):
        super().__init__(message)
