class PresentationException(Exception):
    """プレゼンテーション例外の基底クラス"""

    status_code: int = 400  # デフォルト: Bad Request

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
