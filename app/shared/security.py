from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли введенный пароль сохраненному хешу."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль для безопасного хранения.
    Использует pwdlib для надежного хеширования.
    """
    return password_hash.hash(password)


def create_access_token(data: dict) -> str:
    """
    Генерирует JWT токен с данными пользователя и временем истечения.

    Время жизни токена берётся из настроек (ACCESS_TOKEN_EXPIRE_MINUTES).
    Конвертирует UUID в строку, если 'sub' — это UUID.
    """
    to_encode = data.copy()

    if isinstance(to_encode.get("sub"), UUID):
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    """Декодирует JWT токен и возвращает идентификатор пользователя (sub).
    Если токен недействителен, возвращает None.
    Без участия БД.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
