
class AppError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.user_message = message
