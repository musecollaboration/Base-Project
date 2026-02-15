from abc import ABC

from app.domain.exceptions.base import DomainException
from app.domain.interfaces.unit_of_work import IUnitOfWork
from app.shared.logging import logger


class BaseUseCase(ABC):
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def execute(self, *args, **kwargs):
        # Транзакция уже открыта на уровне dependency (get_uow)
        # BaseUseCase только выполняет бизнес-логику,
        # commit/rollback делает UoW.__aexit__
        try:
            result = await self._run(*args, **kwargs)
            return result
        except DomainException as e:
            logger.warning(f"Бизнес-ошибка в {self.__class__.__name__}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Критический сбой в {self.__class__.__name__}")
            raise
