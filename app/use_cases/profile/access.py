"""Use Cases для управления доступом пользователя."""

from uuid import UUID

from app.domain.entities.user import User
from app.domain.exceptions import UserNotFound
from app.shared.logging import logger
from app.use_cases.base import BaseUseCase


class DisableUserUseCase(BaseUseCase):
    """Use Case для отключения пользователя."""

    async def _run(self, user_id: UUID) -> User:
        """Отключить пользователя."""
        user = await self.uow.users.get_by_id(user_id)

        if not user:
            logger.warning(f"Попытка отключить несуществующего пользователя: {user_id}")
            raise UserNotFound()

        # Применяем бизнес-логику (метод внутри сущности User)
        user.disable()

        # Сохраняем изменения (BaseUseCase сам сделает commit)
        await self.uow.users.update_user(user)

        logger.info(f"Пользователь {user.id} успешно деактивирован")
        return user


class EnableUserUseCase(BaseUseCase):
    """Use Case для активации пользователя."""

    async def _run(self, user_id: UUID) -> User:
        """Активировать пользователя."""
        user = await self.uow.users.get_by_id(user_id)

        if not user:
            logger.warning(
                f"Попытка активировать несуществующего пользователя: {user_id}"
            )
            raise UserNotFound()

        # Применяем бизнес-логику (метод внутри сущности User)
        user.enable()

        # Сохраняем изменения (BaseUseCase сам сделает commit)
        await self.uow.users.update_user(user)

        logger.info(f"Пользователь {user.id} успешно активирован")
        return user
