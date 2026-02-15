from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,  # Берем из конфига
    pool_pre_ping=True,
    # Production: отключить echo, увеличить pool_size
    pool_size=10 if settings.is_prod else 5,
    max_overflow=20 if settings.is_prod else 10,
)

# expire_on_commit=False: объекты не становятся "истёкшими" после commit.
# Это правильно для async SQLAlchemy — сессия остаётся открытой,
# и мы можем продолжать работать с объектами без повторной загрузки из БД.
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
