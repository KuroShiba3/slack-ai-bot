from src.domain.exception.base import DomainException


class DomainServiceException(DomainException):
    pass


class UnknownAgentError(DomainServiceException):
    """不明なエージェントが指定された場合の例外"""

    status_code = 400

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        message = f"不明なエージェントです: {agent_name}"
        super().__init__(message)


class TaskResultNotFoundError(DomainServiceException):
    """タスク結果が存在しない場合の例外"""

    status_code = 422

    def __init__(self, message: str = "タスク結果が存在しません"):
        super().__init__(message)
