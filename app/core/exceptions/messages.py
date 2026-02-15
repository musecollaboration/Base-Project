from dataclasses import dataclass


@dataclass(frozen=True)
class AuthMessages:
    INVALID_TOKEN: str = "Невалидный токен или срок действия истек"
    USER_NOT_FOUND: str = "Пользователь, связанный с данным токеном, не найден"
    USER_DISABLED: str = "Учетная запись отключена"


auth_messages = AuthMessages()

