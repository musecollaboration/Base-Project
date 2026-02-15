from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.dependencies import UOWDep

# Домен и исключения
from app.core.exceptions.auth import AuthUserNotFound, InvalidToken
from app.domain.entities.user import User
from app.domain.exceptions import EmailNotVerified, UserNotFound

# Общие инструменты
from app.shared.logging import logger
from app.shared.security import decode_access_token
from app.use_cases.auth.authenticate import AuthenticateUserUseCase
from app.use_cases.auth.register import RegisterUserUseCase
from app.use_cases.profile.get import GetUserUseCase
from app.use_cases.profile.update import UpdateUserUseCase

# --- Зависимость для получения текущего пользователя из токена ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/")


# --- Фабрики Use Cases (Application Layer) ---


def get_register_use_case(uow: UOWDep) -> RegisterUserUseCase:
    return RegisterUserUseCase(uow)


def get_authenticate_use_case(uow: UOWDep) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(uow)


def get_user_use_case(uow: UOWDep) -> GetUserUseCase:
    return GetUserUseCase(uow)


def get_update_user_use_case(uow: UOWDep) -> UpdateUserUseCase:
    return UpdateUserUseCase(uow)


# --- Логика получения пользователя ---


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_use_case: GetUserUseCase = Depends(get_user_use_case),
) -> User:
    """Получить текущего пользователя из токена."""
    user_id_str = decode_access_token(token)
    if not user_id_str:
        logger.warning("Попытка доступа с невалидным токеном")
        raise InvalidToken()

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.error(f"В токене лежит невалидный UUID: {user_id_str}")
        raise InvalidToken()

    try:
        user: User | None = await user_use_case.execute(user_id)
        if not user:
            raise UserNotFound()
        return user
    except UserNotFound:
        logger.error(f"Токен валиден, но пользователь ID {user_id} не найден в базе")
        raise AuthUserNotFound()


async def get_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверить, что email пользователя подтвержден."""
    if not current_user.is_email_verified:
        logger.warning(
            f"Пользователь {current_user.username} (ID {current_user.id}) "
            f"пытается войти без подтвержденного email"
        )
        raise EmailNotVerified()
    return current_user


# --- Алиасы для удобства в роутерах ---

GetRegisterUseCaseDep = Annotated[RegisterUserUseCase, Depends(get_register_use_case)]

GetAuthenticateUseCaseDep = Annotated[
    AuthenticateUserUseCase, Depends(get_authenticate_use_case)
]

GetUpdateUserUseCaseDep = Annotated[
    UpdateUserUseCase, Depends(get_update_user_use_case)
]

GetCurrentUserDep = Annotated[User, Depends(get_current_user)]

GetVerifiedUserDep = Annotated[User, Depends(get_verified_user)]
