from datetime import datetime
from uuid import UUID

from pydantic import EmailStr

from app.api.v1.schemas.auth import BaseSchema


class UserResponse(BaseSchema):
    id: UUID
    username: str
    email: EmailStr
    disabled: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseSchema):
    username: str | None = None
    email: EmailStr | None = None
    current_password: str
    new_password: str | None = None
