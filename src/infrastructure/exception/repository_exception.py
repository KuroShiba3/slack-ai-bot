from src.infrastructure.exception.base import InfrastructureException


class RepositoryException(InfrastructureException):
    pass


class RepositorySaveError(RepositoryException):
    """エンティティの保存に失敗した場合の例外"""

    status_code = 500

    def __init__(self, entity_name: str, original_error: Exception | None = None):
        self.entity_name = entity_name
        self.original_error = original_error
        message = f"{entity_name}の保存に失敗しました"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)


class RepositoryFetchError(RepositoryException):
    """エンティティの取得に失敗した場合の例外"""

    status_code = 500

    def __init__(self, entity_name: str, original_error: Exception | None = None):
        self.entity_name = entity_name
        self.original_error = original_error
        message = f"{entity_name}の取得に失敗しました"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)


class RepositoryDeleteError(RepositoryException):
    """エンティティの削除に失敗した場合の例外"""

    status_code = 500

    def __init__(self, entity_name: str, original_error: Exception | None = None):
        self.entity_name = entity_name
        self.original_error = original_error
        message = f"{entity_name}の削除に失敗しました"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)
