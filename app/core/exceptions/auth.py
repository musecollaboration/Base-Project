from app.core.exceptions.base import AppError
from app.core.exceptions.messages import auth_messages


class AuthError(AppError):
    """Базовое исключение для авторизации (401)"""

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class InvalidToken(AuthError):
    """Когда токен 'просрочен', подделан или отсутствует"""

    message: str = auth_messages.INVALID_TOKEN


# Это исключение нужно, если токен валиден, но запись о юзере внезапно исчезла из БД
class AuthUserNotFound(AuthError):
    """Пользователь из токена не найден"""

    message: str = auth_messages.USER_NOT_FOUND
