from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import (
    UserRepository as UserRepositoryInterface,
)
from app.infrastructure.database.models.user import UserORM
from app.infrastructure.mappers.user_mapper import UserMapper
from app.shared.logging import logger


class UserRepository(UserRepositoryInterface):
    """Реализация репозитория пользователей. Транзакциями управляет Unit of Work."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> User | None:
        """Получить пользователя по ID."""
        try:
            # Используем session.get — это быстрее, если объект уже в памяти
            orm_user = await self.session.get(UserORM, id)
            return UserMapper.to_domain(orm_user) if orm_user else None
        except SQLAlchemyError:
            logger.exception(f"Ошибка БД при поиске по ID: {id}")
            raise

    async def get_by_username(self, username: str) -> User | None:
        """Получить пользователя по username."""
        try:
            stmt = select(UserORM).where(UserORM.username == username)
            result = await self.session.execute(stmt)
            orm_user = result.scalar_one_or_none()
            return UserMapper.to_domain(orm_user) if orm_user else None
        except SQLAlchemyError:
            logger.exception(f"Ошибка БД при поиске по username: {username}")
            raise

    async def get_by_email(self, email: str) -> User | None:
        """Получить пользователя по email."""
        try:
            stmt = select(UserORM).where(UserORM.email == email)
            result = await self.session.execute(stmt)
            orm_user = result.scalar_one_or_none()
            return UserMapper.to_domain(orm_user) if orm_user else None
        except SQLAlchemyError:
            logger.exception(f"Ошибка БД при поиске по email: {email}")
            raise

    async def create_user(self, user: User) -> None:
        """
        Добавить нового пользователя в сессию.

        Примечание: commit делает UoW.__aexit__() автоматически.
        """
        try:
            user_orm = UserMapper.to_orm(user)
            self.session.add(user_orm)
        except SQLAlchemyError:
            logger.exception("Критическая ошибка БД при добавлении пользователя")
            raise

    async def update_user(self, user: User) -> None:
        """Синхронизировать состояние доменной сущности с ORM-объектом."""
        try:
            # session.get() уже проверяет Identity Map и БД
            orm_user = await self.session.get(UserORM, user.id)

            if orm_user:
                UserMapper.update_orm_from_domain(orm_user, user)
            else:
                logger.warning(
                    f"Попытка обновить несуществующего пользователя: {user.id}"
                )
        except SQLAlchemyError:
            logger.exception(f"Ошибка БД при обновлении пользователя: {user.id}")
            raise
