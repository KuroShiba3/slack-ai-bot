class ApplicationException(Exception):
    status_code: int = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
