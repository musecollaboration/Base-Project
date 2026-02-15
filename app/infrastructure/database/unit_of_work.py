from app.domain.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.repositories.user import UserRepository

# Сюда будешь добавлять импорты новых репозиториев по мере их создания
# from app.infrastructure.repositories.bonus import BonusRepository


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Реализация Unit of Work на базе SQLAlchemy с ленивой загрузкой репозиториев.
    Гарантирует, что все репозитории используют одну и ту же сессию БД.
    """

    def __init__(self, async_session_maker):
        self._async_session_maker = async_session_maker
        # Сами объекты репозиториев здесь не храним,
        # только сессию после входа в контекст

    async def __aenter__(self):
        """Вход в контекстный менеджер: создание сессии."""
        self._session = self._async_session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера: commit при успехе, rollback при ошибке."""
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self._session.close()

    # --- Ленивая инициализация репозиториев через @property ---

    @property
    def users(self) -> UserRepository:
        """Репозиторий пользователей."""
        if not hasattr(self, "_users"):
            # Создаем экземпляр только при первом обращении
            self._users = UserRepository(self._session)
        return self._users

    # Пример добавления нового репозитория:
    # @property
    # def bonuses(self) -> BonusRepository:
    #     if not hasattr(self, '_bonuses'):
    #         self._bonuses = BonusRepository(self._session)
    #     return self._bonuses

    # --- Методы управления транзакциями ---

    async def commit(self):
        """Зафиксировать все изменения, сделанные всеми репозиториями."""
        await self._session.commit()

    async def rollback(self):
        """Откатить все изменения текущей транзакции."""
        await self._session.rollback()
