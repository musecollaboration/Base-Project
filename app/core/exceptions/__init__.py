"""
Core exceptions - технические исключения для инфраструктурного слоя.

Доменные исключения (UserNotFound, UserDisabled, InvalidCredentials)
перенесены в app.domain.exceptions.
"""

from app.core.exceptions.auth import (
    AuthError,
    AuthUserNotFound,
    InvalidToken,
)
from app.core.exceptions.base import AppError

__all__ = [
    "AppError",
    "AuthError",
    "AuthUserNotFound",
    "InvalidToken",
]
