from dataclasses import dataclass


@dataclass(frozen=True)
class UserMessages:
    USERNAME_ALREADY_EXISTS: str = "Пользователь с таким именем уже существует"
    EMAIL_ALREADY_EXISTS: str = "Пользователь с таким email уже существует"
    NOT_FOUND: str = "Пользователь не найден"
    NOT_FOUND_CREDENTIALS: str = "Неверные учетные данные"
    DISABLED: str = "Учетная запись пользователя отключена"
    INVALID_EMAIL: str = "Неверный формат адреса электронной почты"
    INVALID_USERNAME: str = "Имя пользователя должно быть от 4 до 10 символов"
    INVALID_PASSWORD: str = "Пароль слишком слабый или короткий"
    DOMAIN_ERROR: str = "Произошла ошибка бизнес-логики"
    EMAIL_NOT_VERIFIED: str = "Пожалуйста, подтвердите ваш email перед входом."
    INVALID_CURRENT_PASSWORD: str = "Текущий пароль указан неверно"


user_messages = UserMessages()

