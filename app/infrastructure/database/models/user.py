import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, CheckConstraint, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UserORM(Base):
    __tablename__ = "users"

    # Параметры таблицы: индексы и чеки
    __table_args__ = (
        # 1. Составной индекс (ускоряет поиск по почте + статусу верификации)
        Index("ix_users_email_verified", "email", "is_email_verified"),
        # 2. Ограничение на уровне БД (username не может быть короче 4 символов)
        CheckConstraint("char_length(username) >= 4", name="username_min_length"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),  # Оптимальная длина для email
        unique=True,  # Чтобы нельзя было создать два аккаунта на одну почту
        nullable=False,  # Почта обязательна
        index=True,  # Ускоряет поиск пользователя при логине
    )
    disabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,  # Объект в Python сразу был активным
        server_default="false",  # В БД будет false всем старым юзерам
        nullable=False,
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",  # В базе данных по дефолту будет false
        default=False,  # В SQLAlchemy объекте по дефолту будет False
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # База сама поставит текущее время при INSERT
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
