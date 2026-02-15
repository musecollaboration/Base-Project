from abc import ABC, abstractmethod

from app.domain.interfaces.user_repository import UserRepository


class IUnitOfWork(ABC):
    users: UserRepository
    # bonuses: BonusRepository  <-- Когда появится, добавишь сюда

    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def rollback(self): ...
