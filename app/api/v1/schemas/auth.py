from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.v1.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    username: str = Field(..., min_length=4, max_length=10, example="user")
    password: str = Field(..., min_length=8, example="User1234")


class RegisterRequest(LoginRequest):
    email: EmailStr = Field(..., max_length=255, example="user@example.com")


class RegisterResponse(BaseSchema):
    id: UUID
    username: str
    email: EmailStr
    disabled: bool = False
    is_email_verified: bool = False
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str
