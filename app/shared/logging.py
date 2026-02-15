import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import settings

# 1. Контекстная переменная для хранения correlation_id (потокобезопасно в async)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    correlation_id_var.set(correlation_id)


# 2. Форматтеры


class JSONFormatter(logging.Formatter):
    """Форматтер для Prod (ELK / Loki)."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Форматтер для Dev (красивый вывод в консоль)."""

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = self.formatTime(record, self.datefmt)
        corr_id = get_correlation_id()
        # Ставим ID сразу после уровня лога для удобства чтения
        corr_str = f" [{corr_id}]" if corr_id else " [no-id]"

        return (
            f"{record.asctime} | {record.levelname:8s}{corr_str} | "
            f"{record.name}:{record.funcName}:{record.lineno} - {record.getMessage()}"
        )


# 3. Настройка

# Флаг для предотвращения повторной инициализации хендлеров
_logging_initialized = False


def setup_logging():
    """
    Централизованная настройка всех логгеров.

    Вызывается один раз при старте приложения (lifespan).
    Повторные вызовы игнорируются для предотвращения утечки хендлеров.
    """
    global _logging_initialized

    # Защита от повторной инициализации
    if _logging_initialized:
        return

    root_logger = logging.getLogger()

    # Уровень из настроек
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Выбор формата
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(datefmt="%H:%M:%S")

    # Очистка и создание хендлеров
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Файлы
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Убираем лишний спам от библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Помечаем как инициализированное
    _logging_initialized = True


# Создаем именованный логгер для использования в приложении
logger = logging.getLogger("app")
