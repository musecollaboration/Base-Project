# Импортируем напрямую из файлов через относительные пути
from app.domain.exceptions.base import DomainException
from app.domain.exceptions.users import (
    EmailAlreadyExists,
    EmailNotVerified,
    InvalidCredentials,
    InvalidEmailFormat,
    InvalidPasswordException,
    InvalidPasswordFormat,
    InvalidUsernameFormat,
    UserDisabled,
    UsernameAlreadyExists,
    UserNotFound,
)

# Теперь перечисляем их в __all__
__all__ = [
    "DomainException",
    "UserNotFound",
    "UserDisabled",
    "InvalidEmailFormat",
    "InvalidUsernameFormat",
    "InvalidPasswordFormat",
    "InvalidCredentials",
    "EmailAlreadyExists",
    "UsernameAlreadyExists",
    "EmailNotVerified",
    "InvalidPasswordException",
]
