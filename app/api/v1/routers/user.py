from fastapi import APIRouter, status

from app.api.v1.dependencies import (
    GetCurrentUserDep,
    GetUpdateUserUseCaseDep,
    GetVerifiedUserDep,
)
from app.api.v1.schemas.user import UserResponse, UserUpdateRequest
from app.use_cases.profile.update import UpdateUserDTO

router = APIRouter()


@router.get("/me/", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def read_users_me(current_user: GetCurrentUserDep) -> UserResponse:
    """Получение информации о текущем пользователе."""
    # Контроллер преобразует доменную сущность в DTO
    return UserResponse.model_validate(current_user)


@router.get(
    "/me/verified/", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def read_verified_user(verified_current_user: GetVerifiedUserDep) -> UserResponse:
    """Получение информации о текущем пользователе с проверкой подтверждения email."""
    # Контроллер преобразует доменную сущность в DTO
    return UserResponse.model_validate(verified_current_user)


@router.post(
    "/update-user", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def update_user(
    update_data: UserUpdateRequest,
    verified_current_user: GetVerifiedUserDep,
    update_user_use_case: GetUpdateUserUseCaseDep,
) -> UserResponse:
    """Обновление информации о текущем пользователе."""
    dto = UpdateUserDTO(**update_data.model_dump())
    updated_user = await update_user_use_case.execute(verified_current_user, dto)
    return UserResponse.model_validate(updated_user)
