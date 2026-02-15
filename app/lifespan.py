from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from app.core.config import settings
from app.infrastructure.database.engine import engine
from app.shared.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст управления жизненным циклом приложения FastAPI."""

    import sqlalchemy as sa

    # --- Действия при СТАРТЕ приложения ---
    # Проверяем соединение с БД

    logger.info(f"🚀 API запускается... [{settings.ENVIRONMENT}]")

    try:
        setup_logging()
        # Пытаемся выполнить тестовый запрос
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
        logger.info(f"✅ Соединение с БД успешно установлено ({settings.DATABASE_URL})")
    except asyncpg.exceptions.InvalidPasswordError as e:
        logger.error(
            "❌ Неверный пароль или имя пользователя для подключения к БД! "
            "Проверьте настройки DATABASE_URL."
        )
        raise e
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        # Здесь можно либо просто логировать, либо остановить приложение
        raise e

    yield  # Здесь приложение "работает"

    # --- Действия при ВЫКЛЮЧЕНИИ приложения ---
    # Закрываем пулы соединений, чтобы не было утечек
    logger.info("🛑 API закрывается...")
    await engine.dispose()
    logger.info("✅ Пул подключений к БД закрыт.")
