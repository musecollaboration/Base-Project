from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.v1.schemas.auth import BaseSchema


class UserResponse(BaseSchema):
    id: UUID = Field(description="Уникальный идентификатор пользователя")
    username: str = Field(description="Имя пользователя")
    email: EmailStr = Field(description="Email адрес пользователя")
    disabled: bool = Field(description="Статус блокировки")
    is_email_verified: bool = Field(description="Статус email")
    created_at: datetime = Field(description="Дата создания аккаунта")
    updated_at: datetime = Field(description="Дата обновления")


class UserUpdateRequest(BaseSchema):
    username: str | None = Field(
        default=None,
        min_length=4,
        max_length=10,
        example="newuser",
        description="Новое имя пользователя (от 4 до 10 символов)"
    )
    email: EmailStr | None = Field(
        default=None,
        max_length=255,
        example="new@example.com",
        description="Новый email адрес"
    )
    current_password: str = Field(
        ...,
        min_length=8,
        example="******",
        description="Текущий пароль для подтверждения",
        json_schema_extra={"writeOnly": True}
    )
    new_password: str | None = Field(
        default=None,
        min_length=8,
        example="******",
        description="Новый пароль (минимум 8 символов)",
        json_schema_extra={"writeOnly": True}
    )
