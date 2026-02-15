"""Use Case для регистрации пользователя."""

from dataclasses import dataclass

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
        """Создать нового пользователя."""

        # 1. Проверка уникальности (Оставляем в Use Case, т.к. нужен доступ к БД)
        if await self.uow.users.get_by_username(dto.username):
            raise UsernameAlreadyExists()

        if await self.uow.users.get_by_email(dto.email):
            raise EmailAlreadyExists()

        # 2. Создаем доменную сущность.
        # ВНИМАНИЕ: Если в DTO пришли битые данные, UserIdentity выкинет DomainException
        # (InvalidUsernameFormat / InvalidEmailFormat) прямо здесь.
        new_user: User = User.create(username=dto.username, email=dto.email)

        # 2.1. Валидация пароля через Value Object
        password = Password(dto.password)

        # 3. Хешируем пароль
        hashed = get_password_hash(password.value)
        new_user.set_password(hashed)

        # 4. Сохранение (Репозиторий использует Маппер внутри)
        await self.uow.users.create_user(new_user)

        # 5. Когда добавишь NewRepository в UoW
        # К этому моменту транзакция еще открыта.
        # await self.uow.bonuses.create_bonus_account(
        #     user_id=new_user.id,
        #     initial_balance=100
        # )

        # Комментарий: commit выполнится автоматически в BaseUseCase
        logger.info(f"Пользователь подготовлен: {new_user.username} (ID={new_user.id})")

        return new_user
