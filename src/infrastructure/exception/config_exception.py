from src.infrastructure.exception.base import InfrastructureException


class ConfigException(InfrastructureException):
    pass


class MissingEnvironmentVariableError(ConfigException):
    """環境変数が設定されていない場合の例外"""

    status_code = 500

    def __init__(self, variable_names: list[str]):
        self.variable_names = variable_names
        variables_str = ", ".join(variable_names)
        message = f"環境変数が設定されていません: {variables_str}"
        super().__init__(message)
