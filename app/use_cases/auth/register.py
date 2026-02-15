"""Use Case для регистрации пользователя."""

from dataclasses import dataclass

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from app.domain.entities.user import User
from app.domain.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.domain.value_objects.password import Password
from app.shared.logging import logger
from app.shared.security import get_password_hash
from app.use_cases.base import BaseUseCase


@dataclass(frozen=True)
class RegisterUserDTO:
    username: str
    email: str
    password: str


class RegisterUserUseCase(BaseUseCase):
    """Use Case для создания пользователя."""

    async def _run(self, dto: RegisterUserDTO) -> User:
        """
        Создать нового пользователя.

        Стратегия защиты от race condition (гибридный подход):
        1. Быстрая проверка в БД — только для UX (мгновенная ошибка без вставки)
        2. UNIQUE constraint в БД — реальная защита от гонки
        3. Обработка IntegrityError — преобразует ошибку БД в доменную
        """

        # 1. Быстрая проверка уникальности (для UX — мгновенная ошибка)
        if await self.uow.users.get_by_username(dto.username):
            raise UsernameAlreadyExists()

        if await self.uow.users.get_by_email(dto.email):
            raise EmailAlreadyExists()

        # 2. Создаем доменную сущность.
        # ВНИМАНИЕ: Если в DTO пришли битые данные, UserIdentity выкинет DomainException
        # (InvalidUsernameFormat / InvalidEmailFormat) прямо здесь.
        new_user: User = User.create(username=dto.username, email=dto.email)

        # 3. Валидация пароля через Value Object
        password = Password(dto.password)

        # 4. Хешируем пароль
        hashed = get_password_hash(password.value)
        new_user.set_password(hashed)

        # 5. Сохранение с защитой от race condition
        try:
            await self.uow.users.create_user(new_user)
            # commit выполнится автоматически в UoW.__aexit__()

        except IntegrityError as e:
            # Проверяем, что это именно UNIQUE violation
            if not isinstance(e.orig, UniqueViolationError):
                raise

            error_msg = str(e.orig).lower()

            # PostgreSQL имена constraints: ix_users_username, ix_users_email
            if "ix_users_username" in error_msg:
                raise UsernameAlreadyExists() from e
            if "ix_users_email" in error_msg:
                raise EmailAlreadyExists() from e

            # Другая IntegrityError — прокидываем дальше
            raise

        logger.info(f"Пользователь подготовлен: {new_user.username} (ID={new_user.id})")

        return new_user
