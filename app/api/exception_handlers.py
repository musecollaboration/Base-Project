"""
Обработчики доменных исключений для FastAPI.

Преобразуют доменные исключения в HTTP-ответы.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.domain.exceptions import DomainException
from app.shared.logging import get_correlation_id, logger


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Универсальный обработчик всех доменных исключений."""
    logger.warning(
        f"Domain exception: {exc.__class__.__name__} - {exc.message} "
        f"[path: {request.url.path}]"
    )
    correlation_id = get_correlation_id()

    content = {
        "detail": exc.message,
    }

    # В dev показать тип исключения для отладки
    if settings.is_dev:
        content["exception_type"] = exc.__class__.__name__

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"X-Correlation-ID": correlation_id},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Безопасный обработчик ошибок валидации.
    Удаляет 'input' (особенно важно для паролей) и упрощает структуру.
    """
    correlation_id = get_correlation_id()

    sanitized_errors = []
    for error in exc.errors():
        # Убираем 'input' из ошибки для безопасности
        error_data = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
        }
        # Если хочешь совсем упростить, можно оставить только msg и loc
        sanitized_errors.append(error_data)

    logger.warning(f"Validation error [path: {request.url.path}]: {sanitized_errors}")

    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации данных", "errors": sanitized_errors},
        headers={"X-Correlation-ID": str(correlation_id) if correlation_id else None},
    )
