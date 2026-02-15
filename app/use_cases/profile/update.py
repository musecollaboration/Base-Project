from dataclasses import dataclass

from app.domain.entities.user import User
from app.domain.exceptions.users import (
    EmailAlreadyExists,
    InvalidPasswordException,
    UsernameAlreadyExists,
)
from app.domain.value_objects.password import Password
from app.shared.logging import logger
from app.shared.security import get_password_hash, verify_password
from app.use_cases.base import BaseUseCase


@dataclass(frozen=True)
class UpdateUserDTO:
    current_password: str
    username: str | None = None
    email: str | None = None
    new_password: str | None = None


class UpdateUserUseCase(BaseUseCase):
    """Use Case для обновления профиля пользователя."""

    async def _run(self, user: User, dto: UpdateUserDTO) -> User:
        # 1. Валидация прав (Fail Fast)
        if not verify_password(dto.current_password, user.hashed_password):
            logger.warning(f"Неверный пароль при обновлении: user_id={user.id}")
            raise InvalidPasswordException()

        has_changes = False

        # 2. Проверка и обновление Username
        if dto.username is not None and dto.username != user.username:
            if await self.uow.users.get_by_username(dto.username):
                raise UsernameAlreadyExists()
            user.change_username(dto.username)
            has_changes = True

        # 3. Проверка и обновление Email
        if dto.email is not None and dto.email != user.email:
            if await self.uow.users.get_by_email(dto.email):
                raise EmailAlreadyExists()
            user.change_email(dto.email)
            has_changes = True

        # 4. Обновление пароля
        if dto.new_password is not None:
            # Валидация сложности пароля через Password VO
            # (Вызовет InvalidPasswordFormat при ошибке)
            password = Password(dto.new_password)
            user.set_password(get_password_hash(password.value))
            has_changes = True

        # 5. Сохранение
        if has_changes:
            # Просто просим репозиторий подготовить обновление.
            # BaseUseCase сам поймает ошибки, сделает rollback или commit.
            await self.uow.users.update_user(user)
            logger.info(f"Данные пользователя {user.id} подготовлены к сохранению")

        return user
