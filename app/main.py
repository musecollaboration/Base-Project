from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.exception_handlers import (
    domain_exception_handler,
    validation_exception_handler,
)
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.domain.exceptions import DomainException
from app.lifespan import lifespan
from app.shared.logging import (
    get_correlation_id,
    logger,
    set_correlation_id,
    setup_logging,
)

# 1. Сначала настраиваем логи
setup_logging()

# 2. Создаем экземпляр приложения
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.is_dev else None,  # Скрыть документацию в prod
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/openapi.json" if settings.is_dev else None,
)

# --- БЛОК ОБРАБОТЧИКОВ ИСКЛЮЧЕНИЙ ---


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Универсальный обработчик всех технических исключений (AppError)."""
    logger.warning(
        f"App exception: {exc.__class__.__name__} - {exc.message} "
        f"[path: {request.url.path}]"
    )

    correlation_id = get_correlation_id()
    content = {"detail": exc.message}

    if settings.is_dev:
        content["exception_type"] = exc.__class__.__name__

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"X-Correlation-ID": str(correlation_id) if correlation_id else None},
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    """Глобальный перехват необработанных ошибок (500)."""
    # logger.exception запишет трейсбэк, что очень важно для диагностики
    logger.exception(f"Необработанное исключение: {exc}")

    correlation_id = get_correlation_id()
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
        headers={"X-Correlation-ID": str(correlation_id) if correlation_id else None},
    )


# Доменный хендлер импортирован, поэтому регистрируем его так:
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# --- MIDDLEWARES ---


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware для управления сквозным ID запроса."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


if settings.is_dev:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )


# --- РОУТЫ ---


@app.get("/healthcheck")
async def healthcheck():
    """Простой эндпоинт для проверки работоспособности сервиса."""
    logger.info("Вызван эндпоинт healthcheck")
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG if settings.is_dev else None,
    }


# Подключаем основной роутер
app.include_router(api_v1_router)
