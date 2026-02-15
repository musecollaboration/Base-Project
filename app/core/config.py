from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Базовые настройки приложения"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Окружение
    ENVIRONMENT: Literal["dev", "prod", "test"] = "dev"

    # App
    APP_NAME: str = "Base APP"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "dev"

    @property
    def is_prod(self) -> bool:
        return self.ENVIRONMENT == "prod"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"


settings = Settings()
