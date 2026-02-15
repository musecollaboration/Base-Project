"""Use Case для получения пользователя."""

from uuid import UUID

from app.domain.entities.user import User
from app.domain.exceptions import UserDisabled, UserNotFound
from app.shared.logging import logger
from app.use_cases.base import BaseUseCase

"""Use Case для получения пользователя."""


class GetUserUseCase(BaseUseCase):
    """Use Case для получения пользователя с использованием Unit of Work."""

    async def _run(self, id: UUID) -> User:
        """Внутренняя логика получения пользователя."""

        # Обращаемся через uow к нужному репозиторию
        user: User | None = await self.uow.users.get_by_id(id)

        if not user:
            logger.warning(f"Пользователь с ID {id} не найден")
            raise UserNotFound()

        if user.disabled:
            logger.warning(f"Пользователь с ID {id} отключен")
            raise UserDisabled()

        return user
