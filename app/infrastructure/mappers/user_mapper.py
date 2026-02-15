"""Маппер для преобразования между UserORM и доменной сущностью User."""

from app.domain.entities.user import User, UserIdentity, UserSecurity
from app.infrastructure.database.models.user import UserORM


class UserMapper:
    """Маппер для преобразования между слоями инфраструктуры и домена."""

    @staticmethod
    def to_domain(orm: UserORM) -> User:
        """Преобразовать UserORM в доменную сущность User с учетом Value Objects."""
        return User(
            id=orm.id,
            # Собираем Identity (валидация сработает автоматически в __post_init__)
            identity=UserIdentity(
                username=orm.username,
                email=orm.email,
            ),
            # Собираем Security
            security=UserSecurity(
                hashed_password=orm.hashed_password,
                disabled=orm.disabled,
                is_email_verified=orm.is_email_verified,
            ),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    @staticmethod
    def to_orm(user: User) -> UserORM:
        """Преобразовать доменную сущность User в UserORM."""
        # Здесь мы достаем данные из Value Objects через свойства сущности
        return UserORM(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            disabled=user.disabled,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def update_orm_from_domain(orm: UserORM, user: User) -> None:
        """Обновить поля UserORM из доменной сущности User."""
        # Берем данные из User, который достает их из Identity/Security через свойства
        orm.username = user.username
        orm.email = user.email
        orm.hashed_password = user.hashed_password
        orm.disabled = user.disabled
        orm.is_email_verified = user.is_email_verified
        orm.updated_at = user.updated_at
