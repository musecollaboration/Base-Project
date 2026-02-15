class DomainException(Exception):
    """Базовое исключение для всего домена."""

    message: str = "Произошла ошибка бизнес-логики"
    status_code: int = 400

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)
