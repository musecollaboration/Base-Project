from typing import Annotated

from fastapi import Depends

from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

# --- Инфраструктурные зависимости (System Level) ---


async def get_uow():
    """
    Инъекция Unit of Work для управления транзакциями БД.
    Обеспечивает атомарность операций: коммит или откат
    происходят автоматически при завершении жизненного цикла запроса.
    """
    uow = SqlAlchemyUnitOfWork(async_session_maker)
    async with uow:
        yield uow


# Универсальный тип для внедрения UoW в Use Cases и другие зависимости.
# Мы выносим его в core, чтобы избежать циклических импортов между слоями API.
UOWDep = Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)]
