"""Use Case для аутентификации пользователя."""

from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentials, UserDisabled
from app.shared.logging import logger
from app.shared.security import create_access_token, verify_password
from app.use_cases.base import BaseUseCase


class AuthenticateUserUseCase(BaseUseCase):
    """Use Case для аутентификации пользователя."""

    async def _run(self, username: str, password: str) -> dict[str, str]:
        """Аутентифицировать пользователя и вернуть токен."""
        logger.info(f"Попытка входа пользователя: {username}")

        # 1. Поиск пользователя (возвращает User | None)
        user: User | None = await self.uow.users.get_by_username(username)

        # 2. Проверка существования и пароля (Fail Fast)
        if not user or not verify_password(password, user.hashed_password):
            # Мы не уточняем, что именно неверно (логин или пароль) в целях безопасности
            logger.warning(f"Неудачная попытка входа: {username}")
            raise InvalidCredentials()

        # 3. Проверка статуса аккаунта
        if not user.is_enabled:  # Используем свойство из сущности
            logger.warning(f"Вход заблокирован для пользователя: {username}")
            raise UserDisabled()

        # 4. Генерация токена
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
        }

        token = create_access_token(data=token_data)

        logger.info(f"Успешный вход: {username} (ID: {user.id})")

        return {"access_token": token, "token_type": "bearer"}
