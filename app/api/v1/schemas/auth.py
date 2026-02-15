from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.v1.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    username: str = Field(
        ...,
        min_length=4,
        max_length=10,
        example="user",
        description="Имя пользователя (от 4 до 10 символов)"
    )
    password: str = Field(
        ...,
        min_length=8,
        example="******",
        description="Пароль (минимум 8 символов)",
        json_schema_extra={"writeOnly": True}
    )


class RegisterRequest(LoginRequest):
    email: EmailStr = Field(
        ...,
        max_length=255,
        example="user@example.com",
        description="Email адрес пользователя"
    )


class RegisterResponse(BaseSchema):
    id: UUID = Field(description="Уникальный идентификатор пользователя")
    username: str = Field(description="Имя пользователя")
    email: EmailStr = Field(description="Email адрес пользователя")
    disabled: bool = Field(default=False, description="Статус блокировки")
    is_email_verified: bool = Field(default=False, description="Статус email")
    created_at: datetime = Field(description="Дата создания аккаунта")
    updated_at: datetime = Field(description="Дата обновления")


class TokenResponse(BaseSchema):
    access_token: str = Field(description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена (bearer)")
