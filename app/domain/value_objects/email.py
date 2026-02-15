"""
Value Objects для домена.

Примечание: В приложении используется EmailStr от Pydantic для валидации email.
Этот модуль можно использовать для других value objects, если понадобится.
"""

import re

from app.domain.exceptions import InvalidEmailFormat


class Email:
    """Value Object для email с валидацией.

    Не используется напрямую в приложении (используется EmailStr от Pydantic),
    но может быть полезен для доменной логики.
    """

    EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    def __init__(self, value: str):
        if not self.EMAIL_REGEX.match(value):
            raise InvalidEmailFormat(f"Некорректный email: {value}")
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Email):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)
