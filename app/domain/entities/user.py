import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

from app.domain.exceptions import InvalidEmailFormat, InvalidUsernameFormat

# --- Value Object ---


@dataclass(frozen=True)
class UserIdentity:
    """Данные идентификации (Value Object)"""

    username: str
    email: str

    def __post_init__(self):
        # Проверка username (4-10 символов)
        if not self.username or not (4 <= len(self.username) <= 10):
            raise InvalidUsernameFormat()

        # Проверка email
        if "@" not in self.email:
            raise InvalidEmailFormat()


@dataclass(frozen=True)
class UserSecurity:
    """Данные безопасности (Value Object)"""

    hashed_password: str = ""
    disabled: bool = False
    is_email_verified: bool = False


# --- Entity (доменная сущность) ---
class User:
    def __init__(
        self,
        id: UUID,
        identity: UserIdentity,  # Value Object: вместо username и email
        security: UserSecurity,  # Value Object: вместо hashed_password и disabled
        created_at: datetime,
        updated_at: datetime,
    ):
        self._id: UUID = id
        self._identity = identity
        self._security = security
        self._created_at = created_at
        self._updated_at = updated_at

    # --- Properties (Теперь они лезут внутрь объектов-значений) ---
    @property
    def id(self) -> UUID:
        return self._id

    @property
    def username(self) -> str:
        return self._identity.username

    @property
    def email(self) -> str:
        return self._identity.email

    @property
    def hashed_password(self) -> str:
        return self._security.hashed_password

    @property
    def disabled(self) -> bool:
        return self._security.disabled

    @property
    def is_email_verified(self) -> bool:
        return self._security.is_email_verified

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def is_enabled(self) -> bool:
        return not self.disabled

    # --- Фабричный метод ---

    @classmethod
    def create(cls, username: str, email: str) -> "User":
        """
        Фабричный метод для создания нового пользователя
        с валидацией через Value Objects.
        """

        # Валидация произойдет автоматически при создании UserIdentity
        identity = UserIdentity(username=username, email=email)
        # Пароль пока пустой
        security = UserSecurity(disabled=False, is_email_verified=False)

        return cls(
            id=uuid.uuid4(),
            identity=identity,
            security=security,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    # --- Бизнес-логика (Изменяем состояние через замену объектов) ---

    def set_password(self, hashed_password: str):
        """Установить новый хеш пароля. Валидация на пустой пароль."""

        if not hashed_password:
            raise ValueError("Хеш пароля не может быть пустым")
        # Value Object неизменяем (frozen), поэтому создаем новый с измененным полем
        self._security = replace(self._security, hashed_password=hashed_password)
        self._updated_at = datetime.now(timezone.utc)

    def change_username(self, new_username: str):
        """Изменить username."""
        # 1. Меняем Identity (Value Object)
        self._identity = UserIdentity(username=new_username, email=self.email)

        # 2. Обновляем время
        self._updated_at = datetime.now(timezone.utc)

    def change_email(self, new_email: str):
        """Изменить email и сбросить верификацию."""
        # 1. Меняем Identity (Value Object)
        self._identity = UserIdentity(username=self.username, email=new_email)

        # 2. Меняем Security (сбрасываем верификацию)
        self._security = replace(self._security, is_email_verified=False)

        # 3. Обновляем время
        self._updated_at = datetime.now(timezone.utc)

    def enable(self):
        """Активировать пользователя."""
        self._security = replace(self._security, disabled=False)
        self._updated_at = datetime.now(timezone.utc)

    def disable(self):
        """Деактивировать пользователя."""
        self._security = replace(self._security, disabled=True)
        self._updated_at = datetime.now(timezone.utc)

    def mark_email_as_verified(self):
        """Пометить email пользователя как подтвержденный."""
        self._security = replace(self._security, is_email_verified=True)
        self._updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"User(id={self._id}, username={self.username})"
