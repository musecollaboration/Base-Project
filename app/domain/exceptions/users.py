"""
Доменные исключения.

Исключения, связанные с бизнес-логикой домена.
Технические исключения (InvalidToken)
остаются в app.core.exceptions.
"""

from app.domain.exceptions.base import DomainException
from app.domain.exceptions.messages import user_messages


class UsernameAlreadyExists(DomainException):
    """
    Исключение, возникающее при попытке
    создать пользователя с уже существующим именем.
    """

    message = user_messages.USERNAME_ALREADY_EXISTS
    status_code = 409


class EmailAlreadyExists(DomainException):
    """
    Исключение, возникающее при попытке
    создать пользователя с уже существующим email.
    """

    message = user_messages.EMAIL_ALREADY_EXISTS
    status_code = 409


class UserNotFound(DomainException):
    """
    Исключение, возникающее при попытке
    найти несуществующего пользователя.
    """

    message = user_messages.NOT_FOUND
    status_code = 404


class UserDisabled(DomainException):
    """
    Исключение, возникающее при попытке
    взаимодействовать с отключенной учетной записью пользователя.
    """

    message = user_messages.DISABLED
    status_code = 403


class InvalidEmailFormat(DomainException):
    """
    Исключение, возникающее при неверном формате адреса электронной почты.
    """

    message = user_messages.INVALID_EMAIL
    status_code = 400


class InvalidUsernameFormat(DomainException):
    """
    Исключение, возникающее при неверном формате имени пользователя.
    """

    message = user_messages.INVALID_USERNAME
    status_code = 400


class InvalidPasswordFormat(DomainException):
    """Исключение, возникающее при неверном формате пароля."""

    message = user_messages.INVALID_PASSWORD
    status_code = 400


class InvalidCredentials(DomainException):
    """Исключение, возникающее при неверных учетных данных пользователя."""

    message = user_messages.NOT_FOUND_CREDENTIALS
    status_code = 401


class EmailNotVerified(DomainException):
    """Исключение, возникающее при попытке входа с не подтвержденным email."""

    message = user_messages.EMAIL_NOT_VERIFIED
    status_code = 403


class InvalidPasswordException(DomainException):
    """Исключение, возникающее при неверном текущем пароле."""

    message = user_messages.INVALID_CURRENT_PASSWORD
    status_code = 403
