from fastapi import APIRouter, status

from app.api.v1.dependencies import (
    GetAuthenticateUseCaseDep,
    GetRegisterUseCaseDep,
)
from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.core.config import settings
from app.domain.entities.user import User
from app.shared.logging import logger
from app.use_cases.auth.register import RegisterUserDTO

router = APIRouter()


@router.post(
    "/register/", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_schema: RegisterRequest,
    register_use_case: GetRegisterUseCaseDep,
) -> RegisterResponse:
    """Регистрация нового пользователя."""
    logger.info(f"Запрос на регистрацию пользователя: {user_schema.email}")

    # Use Case инкапсулирует всю бизнес-логику и управление транзакциями
    # 1. Модель Pydantic превращается в словарь
    # 2. Словарь распаковывается в конструктор DTO
    dto = RegisterUserDTO(**user_schema.model_dump())
    # В execute передается один объект, а не пачка аргументов
    user_entity: User = await register_use_case.execute(dto)

    if settings.is_dev:
        logger.debug(
            f"Создан пользователь: {user_entity.username}, email={user_entity.email}"
        )

    # Контроллер только преобразует доменную сущность в DTO
    return RegisterResponse.model_validate(user_entity)


@router.post("/login/", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    authenticate_use_case: GetAuthenticateUseCaseDep,
) -> TokenResponse:
    """Аутентификация пользователя и получение токена."""
    result = await authenticate_use_case.execute(payload.username, payload.password)
    return TokenResponse(**result)
