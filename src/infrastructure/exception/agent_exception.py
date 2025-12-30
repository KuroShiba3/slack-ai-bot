from src.infrastructure.exception.base import InfrastructureException


class AgentException(InfrastructureException):
    pass


class MissingStateError(AgentException):
    """ステートに必要なデータが存在しない場合の例外"""

    status_code = 500

    def __init__(self, state_key: str):
        self.state_key = state_key
        message = f"{state_key}がステートに存在しません"
        super().__init__(message)
