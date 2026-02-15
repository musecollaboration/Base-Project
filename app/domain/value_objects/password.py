import re
from dataclasses import dataclass

from app.domain.exceptions.users import InvalidPasswordFormat


@dataclass(frozen=True)
class Password:
    """Value Object для plaintext пароля с валидацией сложности."""

    value: str

    def __post_init__(self):
        if len(self.value) < 8:
            message = "Пароль должен быть минимум 8 символов"
            raise InvalidPasswordFormat(message=message)

        if not re.search(r"[A-Z]", self.value):
            message = "Пароль должен содержать заглавную букву"
            raise InvalidPasswordFormat(message=message)

        if not re.search(r"[a-z]", self.value):
            message = "Пароль должен содержать строчную букву"
            raise InvalidPasswordFormat(message=message)

        if not re.search(r"[0-9]", self.value):
            message = "Пароль должен содержать цифру"
            raise InvalidPasswordFormat(message=message)

    def __str__(self):
        return self.value
