from src.infrastructure.exception.base import InfrastructureException


class LLMException(InfrastructureException):
    pass


class UnsupportedMessageRoleError(LLMException):
    """未対応のメッセージロールの場合の例外"""

    status_code = 500

    def __init__(self, role: str):
        self.role = role
        message = f"未対応のロールです: {role}"
        super().__init__(message)


class UnsupportedModelError(LLMException):
    """未対応のモデル名が指定された場合の例外"""

    status_code = 500

    def __init__(self, model_name: str):
        self.model_name = model_name
        message = f"不明なモデル名が指定されました: {model_name}"
        super().__init__(message)


class UnsupportedMessageTypeError(LLMException):
    """未対応のメッセージタイプの場合の例外"""

    status_code = 500

    def __init__(self, message_type: str):
        self.message_type = message_type
        message = f"未対応のメッセージタイプです: {message_type}"
        super().__init__(message)
