# User Authentication API — Clean Architecture & DDD

Production-ready REST API для регистрации и аутентификации пользователей, построенный на FastAPI с применением принципов Clean Architecture и Domain-Driven Design.

## Оглавление

- [О проекте](#о-проекте)
- [Архитектура](#архитектура)
- [Ключевые особенности](#ключевые-особенности)
- [Структура проекта](#структура-проекта)
- [Слои приложения](#слои-приложения)
- [Технологический стек](#технологический-стек)
- [Установка и запуск](#установка-и-запуск)
- [API документация](#api-документация)
- [Паттерны и практики](#паттерны-и-практики)
- [Дополнительная документация](#дополнительная-документация)

---

## О проекте

Это профессиональный учебный проект, демонстрирующий правильную организацию кода в FastAPI приложении с использованием Clean Architecture и DDD. Проект включает:

- **Регистрацию и аутентификацию** пользователей (JWT + Argon2)
- **Clean Architecture** с четким разделением на слои
- **Domain-Driven Design (DDD)** — Entities, Value Objects, Use Cases, Repositories
- **Unit of Work** паттерн для управления транзакциями
- **Value Objects** с валидацией (Password, Email, UserIdentity, UserSecurity)
- **Use Cases** для инкапсуляции бизнес-логики
- **Dependency Injection** через FastAPI
- **Структурированное логирование** с correlation ID
- **Алембик миграции** для версионирования БД
- **Docker Compose** для локальной разработки

---

## Архитектура

Проект построен на принципах **Clean Architecture** (Чистая архитектура) и **Domain-Driven Design (DDD)**:

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                    │
│              (api/v1/routers, schemas)                  │
│         HTTP запросы, валидация, сериализация           │
└────────────────────┬────────────────────────────────────┘
                     │ зависит от
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                     │
│                    (use_cases/)                         │
│         Оркестрация бизнес-логики, Use Cases            │
└────────────────────┬────────────────────────────────────┘
                     │ зависит от
                     ↓
┌─────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                        │
│    (entities, value_objects, interfaces, exceptions)    │
│     Ядро приложения: бизнес-правила и доменная модель   │
└────────────────────┬────────────────────────────────────┘
                     ↑ реализует (через интерфейсы)
                     │
┌─────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                    │
│     (repositories, database, mappers, unit_of_work)     │
│        PostgreSQL, SQLAlchemy, JWT, внешние сервисы     │
└─────────────────────────────────────────────────────────┘
```

**Ключевые принципы:**

- ✅ **Зависимости направлены внутрь** — Domain Layer не зависит ни от кого
- ✅ **Инверсия зависимостей** — Infrastructure реализует интерфейсы из Domain
- ✅ **Единая ответственность** — каждый слой решает свои задачи
- ✅ **Тестируемость** — бизнес-логику можно тестировать без БД и HTTP

---

## Ключевые особенности

### Unit of Work Pattern

Управление транзакциями на уровне HTTP-запроса с автоматическим commit/rollback:

```python
# dependencies.py
async def get_uow():
    """UoW живет весь HTTP-запрос благодаря yield."""
    uow = SqlAlchemyUnitOfWork(async_session_maker)
    async with uow:  # BEGIN транзакции
        yield uow
    # AUTO commit при успехе, rollback при ошибке
```

**Преимущества:**

- Одна транзакция на весь запрос
- Все Use Cases работают с одной сессией БД
- Автоматическое управление commit/rollback

### Value Objects с валидацией

**Password Value Object** — валидация сложности пароля:

```python
@dataclass(frozen=True)
class Password:
    value: str

    def __post_init__(self):
        # Минимум 8 символов, заглавная + строчная + цифра
        if len(self.value) < 8:
            raise InvalidPasswordFormat("Минимум 8 символов")
        if not re.search(r'[A-Z]', self.value):
            raise InvalidPasswordFormat("Нужна заглавная буква")
```

**UserIdentity & UserSecurity** — композиция в User Entity:

```python
@dataclass(frozen=True)
class UserIdentity:
    username: str  # Валидация в __post_init__
    email: str

@dataclass(frozen=True)
class UserSecurity:
    hashed_password: str = ""
    disabled: bool = False
    is_email_verified: bool = False

class User:
    def __init__(self, id, identity: UserIdentity, security: UserSecurity, ...):
        self._identity = identity
        self._security = security
```

### Use Cases по доменам

Организация Use Cases по бизнес-доменам:

```
use_cases/
├── base.py              # BaseUseCase
├── auth/                # Аутентификация
│   ├── authenticate.py  # Вход, выдача JWT
│   └── register.py      # Регистрация
└── profile/             # Управление профилем
    ├── get.py           # Получение пользователя
    ├── update.py        # Обновление данных
    └── access.py        # Активация/деактивация
```

### DTO Pattern

Все Use Cases принимают DTO (Data Transfer Objects):

```python
@dataclass(frozen=True)
class RegisterUserDTO:
    username: str
    email: str
    password: str

class RegisterUserUseCase(BaseUseCase):
    async def _run(self, dto: RegisterUserDTO) -> User:
        # Валидация пароля через Password VO
        password = Password(dto.password)
        # ...
```

### Mapper Pattern

Изоляция Domain от Infrastructure через маппер:

```python
class UserMapper:
    @staticmethod
    def to_domain(orm: UserORM) -> User:
        """ORM → Domain Entity"""
        return User(
            id=orm.id,
            identity=UserIdentity(username=orm.username, email=orm.email),
            security=UserSecurity(
                hashed_password=orm.hashed_password,
                disabled=orm.disabled,
                is_email_verified=orm.is_email_verified
            ),
            ...
        )

    @staticmethod
    def to_orm(user: User) -> UserORM:
        """Domain Entity → ORM"""
```

### Structured Logging

Логирование с correlation ID для трассировки запросов:

```python
# Каждый HTTP-запрос имеет уникальный ID
19:38:03 | INFO [675151b0-...-4f7cf3e60a43] | app:_run:52 -
  Данные пользователя подготовлены к сохранению
```

---

## Структура проекта

```
Base_Project/
├── app/                              # Исходный код приложения
│   ├── api/                          # 🟢 Presentation Layer (HTTP API)
│   │   ├── exception_handlers.py     # Обработчики исключений
│   │   └── v1/                       # API версии 1
│   │       ├── dependencies.py       # Здесь мы собираем Use Cases, внедряя в них UOWDep из core.
│   │       ├── router.py             # Главный роутер API v1
│   │       ├── routers/              # Эндпоинты
│   │       │   ├── auth.py           # POST /register, /login
│   │       │   └── user.py           # GET /me, POST /update-user
│   │       └── schemas/              # Pydantic схемы (DTO для API)
│   │           ├── auth.py           # RegisterRequest, TokenResponse
│   │           ├── base.py           # BaseSchema
│   │           └── user.py           # UserResponse, UserUpdateRequest
│   │
│   ├── core/                         # 🔴 Core (Конфигурация и глобальные настройки)
│   │   ├── config.py                 # Settings из .env
│   │   │
│   │   │                             # Системные зависимости уровня инфраструктуры.
│   │   ├── dependencies.py           # Здесь определяется Unit of Work и базовые ресурсы (БД, кэш),
│   │   │                             # которые необходимы для работы любого слоя приложения.
│   │   │
│   │   └── exceptions/               # Технические исключения (не доменные)
│   │       ├── auth.py               # InvalidToken, AuthUserNotFound
│   │       ├── base.py               # AppError
│   │       └── messages.py           # Сообщения об ошибках
│   │
│   ├── domain/                       # 🔵 Domain Layer (Бизнес-логика)
│   │   ├── entities/                 # Доменные сущности
│   │   │   └── user.py               # User + UserIdentity + UserSecurity (VOs)
│   │   ├── exceptions/               # Доменные исключения
│   │   │   ├── base.py               # DomainException
│   │   │   ├── messages.py           # Сообщения бизнес-ошибок
│   │   │   └── users.py              # UserNotFound, EmailAlreadyExists, и т.д.
│   │   ├── interfaces/               # Абстрактные интерфейсы (порты)
│   │   │   ├── unit_of_work.py       # IUnitOfWork (ABC)
│   │   │   └── user_repository.py    # UserRepository (ABC)
│   │   ├── value_objects/            # Value Objects (неизменяемые объекты-значения)
│   │   │   ├── email.py              # Email VO (не используется напрямую)
│   │   │   └── password.py           # Password VO с валидацией сложности
│   │   ├── EXAMPLES.py               # Примеры использования Domain Layer
│   │   └── README.md                 # Документация Domain Layer
│   │
│   ├── infrastructure/               # 🟡 Infrastructure Layer
│   │   ├── database/                 # Работа с БД
│   │   │   ├── base.py               # Base для SQLAlchemy
│   │   │   ├── engine.py             # Engine, async_session_maker
│   │   │   ├── unit_of_work.py       # SqlAlchemyUnitOfWork (реализация IUnitOfWork)
│   │   │   └── models/               # ORM-модели
│   │   │       └── user.py           # UserORM (SQLAlchemy)
│   │   ├── mappers/                  # Мапперы Domain ↔ Infrastructure
│   │   │   └── user_mapper.py        # UserMapper (to_domain, to_orm, update_orm)
│   │   └── repositories/             # Реализации репозиториев
│   │       └── user.py               # UserRepository (реализация интерфейса)
│   │
│   ├── shared/                       # 🟣 Shared (Общие утилиты)
│   │   ├── logging.py                # Настройка логирования + correlation_id
│   │   └── security.py               # JWT, хеширование паролей (Argon2)
│   │
│   ├── use_cases/                    # 🔵 Application Layer (Use Cases)
│   │   ├── base.py                   # BaseUseCase
│   │   ├── auth/                     # Домен: аутентификация
│   │   │   ├── authenticate.py       # AuthenticateUserUseCase
│   │   │   └── register.py           # RegisterUserUseCase + RegisterUserDTO
│   │   └── profile/                  # Домен: профиль пользователя
│   │       ├── access.py             # Disable/EnableUserUseCase
│   │       ├── get.py                # GetUserUseCase
│   │       └── update.py             # UpdateUserUseCase + UpdateUserDTO
│   │
│   ├── lifespan.py                   # Lifecycle FastAPI (startup/shutdown)
│   └── main.py                       # Точка входа приложения
│
├── logs/                             # Логи приложения (ротация по дням)
│   └── app.log
├── migrations/                       # Alembic миграции
│   ├── env.py                        # Конфигурация Alembic
│   └── versions/                     # Версии миграций
│       ├── initial_migration.py
├── alembic.ini                       # Конфиг Alembic
├── docker-compose.yml                # PostgreSQL в Docker
├── Makefile                          # Команды для разработки
├── pyproject.toml                    # Poetry зависимости
├── .env.example                      # Пример конфигурации
├── .gitignore                        # Игнорируемые файлы
└── README.md                         # Данный файл
```

---

## Слои приложения

### 🔵 1. Domain Layer (Доменный слой)

**Папка:** [app/domain/](app/domain/)

**Назначение:** Ядро приложения, содержащее бизнес-логику и бизнес-правила. Полностью независим от фреймворков, БД, API.

**Состав:**

- **Entities** ([entities/](app/domain/entities/)) — доменные сущности с бизнес-методами
  - [user.py](app/domain/entities/user.py) — User + UserIdentity + UserSecurity (Value Objects)
- **Value Objects** ([value_objects/](app/domain/value_objects/)) — неизменяемые объекты-значения с валидацией
  - [password.py](app/domain/value_objects/password.py) — Password VO (валидация сложности: мин. 8 символов, заглавная, строчная, цифра)
  - [email.py](app/domain/value_objects/email.py) — Email VO (не используется напрямую)
- **Interfaces** ([interfaces/](app/domain/interfaces/)) — абстрактные интерфейсы (порты)
  - [unit_of_work.py](app/domain/interfaces/unit_of_work.py) — IUnitOfWork (ABC)
  - [user_repository.py](app/domain/interfaces/user_repository.py) — UserRepository (ABC)
- **Exceptions** ([exceptions/](app/domain/exceptions/)) — доменные исключения
  - [base.py](app/domain/exceptions/base.py) — DomainException (базовый класс)
  - [users.py](app/domain/exceptions/users.py) — UserNotFound, EmailAlreadyExists, InvalidPasswordFormat, и т.д.
  - [messages.py](app/domain/exceptions/messages.py) — сообщения бизнес-ошибок

**Ключевые принципы:**

- ✅ **НЕ зависит** от БД, API, фреймворков (инверсия зависимостей)
- ✅ **Use Cases НЕ управляют** транзакциями (это делает UoW через yield)
- ✅ **Use Cases оркеструют** репозитории и Entity
- ✅ **Value Objects валидируют** данные (Password ДО хеширования!)
- ✅ **DTO Pattern** — все Use Cases принимают DTO (frozen dataclass)
- ✅ **Mapper Pattern** — изоляция Domain от Infrastructure
- ✅ Легко тестируется без БД (моки)
- ✅ Можно переиспользовать в CLI, GUI, микросервисах

**Пример User Entity с композицией Value Objects:**

```python
# domain/entities/user.py
@dataclass(frozen=True)
class UserIdentity:
    """Value Object для идентификационных данных."""
    username: str
    email: str

    def __post_init__(self):
        if not (4 <= len(self.username) <= 10):
            raise InvalidUsernameFormat()
        if "@" not in self.email:
            raise InvalidEmailFormat()

@dataclass(frozen=True)
class UserSecurity:
    """Value Object для данных безопасности."""
    hashed_password: str = ""
    disabled: bool = False
    is_email_verified: bool = False

class User:
    """Доменная сущность пользователя (композиция VOs)."""

    def __init__(
        self,
        id: UUID,
        identity: UserIdentity,    # ← Value Object
        security: UserSecurity,    # ← Value Object
        created_at: datetime,
        updated_at: datetime,
    ):
        self._id = id
        self._identity = identity
        self._security = security
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(cls, username: str, email: str) -> "User":
        """Фабричный метод для создания нового пользователя."""
        identity = UserIdentity(username=username, email=email)
        security = UserSecurity(disabled=False, is_email_verified=False)

        return cls(
            id=uuid4(),
            identity=identity,
            security=security,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def disable(self):
        """Деактивировать пользователя."""
        self._security = replace(self._security, disabled=True)
        self._updated_at = datetime.now(timezone.utc)

    def change_email(self, new_email: str):
        """Изменить email и сбросить верификацию."""
        self._identity = UserIdentity(username=self.username, email=new_email)
        self._security = replace(self._security, is_email_verified=False)
        self._updated_at = datetime.now(timezone.utc)
```

**Пример Use Case с Password VO:**

```python
# use_cases/auth/register.py
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from app.domain.value_objects.password import Password

@dataclass(frozen=True)
class RegisterUserDTO:
    """DTO для регистрации пользователя."""
    username: str
    email: str
    password: str

class RegisterUserUseCase(BaseUseCase):
    """Use Case для регистрации нового пользователя."""

    async def _run(self, dto: RegisterUserDTO) -> User:
        # 1. Быстрая проверка бизнес-правил (для UX)
        if await self.uow.users.get_by_username(dto.username):
            raise UsernameAlreadyExists()

        if await self.uow.users.get_by_email(dto.email):
            raise EmailAlreadyExists()

        # 2. Валидация пароля через Password VO (ДО хеширования!)
        password = Password(dto.password)  # ← Валидация: мин. 8 символов, заглавная, строчная, цифра

        # 3. Создание доменной сущности
        new_user = User.create(username=dto.username, email=dto.email)

        # 4. Хеширование валидного пароля
        hashed = get_password_hash(password.value)
        new_user.set_password(hashed)

        # 5. Сохранение с защитой от race condition
        try:
            await self.uow.users.create_user(new_user)
            # ⚡ Commit делает UoW при выходе из контекста (yield в dependencies)

        except IntegrityError as e:
            # Защита от гонки условий (race condition)
            if isinstance(e.orig, UniqueViolationError):
                error_msg = str(e.orig).lower()
                if "ix_users_username" in error_msg:
                    raise UsernameAlreadyExists() from e
                if "ix_users_email" in error_msg:
                    raise EmailAlreadyExists() from e
            raise

        logger.info(f"Пользователь {new_user.username} подготовлен к сохранению")

        return new_user
```

**Пример BaseUseCase (без управления транзакциями):**

```python
# use_cases/base.py
class BaseUseCase(ABC):
    """
    Базовый Use Case.

    ⚡ ВАЖНО: НЕ управляет транзакциями!
    Транзакция открывается через get_uow() с yield в dependencies.py
    Commit/Rollback делает UoW.__aexit__() автоматически.
    """

    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def execute(self, *args, **kwargs):
        """Выполнить Use Case (без commit/rollback)."""
        try:
            result = await self._run(*args, **kwargs)
            return result
        except DomainException as e:
            logger.warning(f"Бизнес-ошибка в {self.__class__.__name__}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Критический сбой в {self.__class__.__name__}")
            raise

    @abstractmethod
    async def _run(self, *args, **kwargs):
        """Бизнес-логика Use Case (должна быть реализована в подклассе)."""
        ...
```

**Примечание:** Use Cases вынесены в отдельную папку [app/use_cases/](app/use_cases/) (Application Layer).

**Документация Domain Layer:** [app/domain/README.md](app/domain/README.md)  
**Примеры использования:** [app/domain/EXAMPLES.py](app/domain/EXAMPLES.py)

---

### 🟡 2. Infrastructure Layer (Инфраструктурный слой)

**Папка:** [app/infrastructure/](app/infrastructure/)

**Назначение:** Реализация технических деталей — работа с БД, внешними API, файлами. Реализует интерфейсы из Domain Layer.

**Состав:**

- **database/** — настройка SQLAlchemy, ORM-модели, Unit of Work
  - [engine.py](app/infrastructure/database/engine.py) — создание async_engine и async_session_maker
  - [base.py](app/infrastructure/database/base.py) — Base для ORM-моделей
  - [unit_of_work.py](app/infrastructure/database/unit_of_work.py) — SqlAlchemyUnitOfWork (реализация IUnitOfWork)
  - [models/user.py](app/infrastructure/database/models/user.py) — UserORM (SQLAlchemy модель)
- **mappers/** — преобразователи Domain Entity ↔ ORM модель
  - [user_mapper.py](app/infrastructure/mappers/user_mapper.py) — UserMapper (to_domain, to_orm, update_orm_from_domain)
- **repositories/** — реализация интерфейсов репозиториев из domain
  - [user.py](app/infrastructure/repositories/user.py) — UserRepository (работает с Domain Entity через Mapper)

**Ключевые принципы:**

- ✅ Реализует интерфейсы из Domain (IUnitOfWork, UserRepository)
- ✅ Знает о конкретных технологиях (PostgreSQL, SQLAlchemy, Argon2)
- ✅ Можно заменить без изменения Domain (Postgres → MongoDB)
- ✅ **Mapper изолирует** Domain от Infrastructure (Domain Entity ↔ ORM)
- ✅ **UoW управляет** транзакциями через `__aenter__` / `__aexit__`

**Пример SqlAlchemyUnitOfWork (с автоматическим COMMIT/ROLLBACK):**

```python
# infrastructure/database/unit_of_work.py
from app.domain.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.repositories.user import UserRepository

class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    Unit of Work для SQLAlchemy.

    ⚡ ВАЖНО: Управляет транзакциями через контекстный менеджер!
    - __aenter__: BEGIN транзакция
    - __aexit__: COMMIT при успехе, ROLLBACK при ошибке
    """

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def __aenter__(self):
        """Вход в контекстный менеджер (BEGIN)."""
        self._session: AsyncSession = self._session_factory()

        # Инициализируем репозитории с одной сессией
        self.users = UserRepository(self._session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Выход из контекстного менеджера (COMMIT или ROLLBACK).

        - Если ошибка (exc_type != None) → ROLLBACK
        - Если успех (exc_type == None) → COMMIT
        """
        try:
            if exc_type is not None:
                await self.rollback()
                logger.warning("Транзакция откачена из-за ошибки")
            else:
                await self.commit()
                logger.info("Транзакция успешно зафиксирована")
        finally:
            await self._session.close()

    async def commit(self):
        """Зафиксировать транзакцию."""
        await self._session.commit()

    async def rollback(self):
        """Откатить транзакцию."""
        await self._session.rollback()
```

**Пример UserRepository (работает с Domain Entity через Mapper):**

```python
# infrastructure/repositories/user.py
from app.domain.interfaces.user_repository import UserRepository as IUserRepository
from app.domain.entities.user import User
from app.infrastructure.mappers.user_mapper import UserMapper

class UserRepository(IUserRepository):
    """Реализация репозитория для работы с PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить пользователя по ID (возвращает Domain Entity)."""
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()

        if not user_orm:
            return None

        # ORM → Domain Entity через Mapper
        return UserMapper.to_domain(user_orm)

    async def create_user(self, user: User) -> None:
        """Создать нового пользователя (принимает Domain Entity)."""
        # Domain Entity → ORM через Mapper
        user_orm = UserMapper.to_orm(user)
        self._session.add(user_orm)

        # ⚡ ВАЖНО: НЕТ commit! Commit делает UoW.__aexit__

    async def update_user(self, user: User) -> None:
        """Обновить существующего пользователя (принимает Domain Entity)."""
        stmt = select(UserORM).where(UserORM.id == user.id)
        result = await self._session.execute(stmt)
        user_orm = result.scalar_one_or_none()

        if not user_orm:
            raise UserNotFound()

        # Обновляем ORM из Domain Entity через Mapper
        UserMapper.update_orm_from_domain(user_orm, user)

        # ⚡ ВАЖНО: НЕТ commit! Commit делает UoW.__aexit__
```

**Пример UserMapper (изоляция Domain от Infrastructure):**

```python
# infrastructure/mappers/user_mapper.py
from app.domain.entities.user import User, UserIdentity, UserSecurity
from app.infrastructure.database.models.user import UserORM

class UserMapper:
    """Mapper для преобразования между Domain Entity и ORM."""

    @staticmethod
    def to_domain(user_orm: UserORM) -> User:
        """ORM → Domain Entity."""
        identity = UserIdentity(
            username=user_orm.username,
            email=user_orm.email,
        )
        security = UserSecurity(
            hashed_password=user_orm.hashed_password,
            disabled=user_orm.disabled,
            is_email_verified=user_orm.is_email_verified,
        )

        return User(
            id=user_orm.id,
            identity=identity,
            security=security,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
        )

    @staticmethod
    def to_orm(user: User) -> UserORM:
        """Domain Entity → ORM."""
        return UserORM(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            disabled=user.disabled,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def update_orm_from_domain(user_orm: UserORM, user: User) -> None:
        """Обновить ORM из Domain Entity (in-place)."""
        user_orm.username = user.username
        user_orm.email = user.email
        user_orm.hashed_password = user.hashed_password
        user_orm.disabled = user.disabled
        user_orm.is_email_verified = user.is_email_verified
        user_orm.updated_at = user.updated_at
```

---

### 🟢 3. Presentation Layer (Слой представления)

**Папка:** [app/api/](app/api/)

**Назначение:** HTTP API — обработка запросов и ответов. Знает только о HTTP, JSON, Pydantic.

**Состав:**

- **v1/** — версия API v1
  - [router.py](app/api/v1/router.py) — главный роутер с подключением всех роутеров
  - [dependencies.py](app/api/v1/dependencies.py) — Dependency Injection (фабрики Use Cases, UoW с yield)
  - **routers/** — эндпоинты FastAPI
    - [auth.py](app/api/v1/routers/auth.py) — регистрация (`POST /register`), логин (`POST /login`)
    - [user.py](app/api/v1/routers/user.py) — получение текущего пользователя (`GET /me`), обновление профиля
  - **schemas/** — Pydantic-схемы для валидации и сериализации
    - [base.py](app/api/v1/schemas/base.py) — базовые схемы (SuccessResponse, ErrorResponse)
    - [auth.py](app/api/v1/schemas/auth.py) — RegisterRequest, RegisterResponse, LoginRequest, TokenResponse
    - [user.py](app/api/v1/schemas/user.py) — UserResponse, UpdateUserRequest
- [exception_handlers.py](app/api/exception_handlers.py) — преобразование доменных исключений в HTTP-ответы

**Ключевые принципы:**

- ✅ Знает только о HTTP, JSON, Pydantic
- ✅ Использует Use Cases для бизнес-логики через DI
- ✅ НЕ содержит бизнес-правил
- ✅ НЕ управляет транзакциями (это делает UoW через yield в dependencies)
- ✅ Работает с Domain Entity, а не с ORM моделями
- ✅ Pydantic схемы ↔ DTO ↔ Domain Entity

**Пример UoW Dependency с yield (управление транзакциями):**

```python
# app/core/dependencies.py
from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

async def get_uow():
    """
    Unit of Work с автоматическим управлением транзакциями.

    ⚡ ВАЖНО: Используется yield для управления жизненным циклом!
    - Транзакция живет ВСЁ время обработки HTTP-запроса
    - async with uow: ... — BEGIN транзакция
    - yield uow — передаём в Use Case
    - Выход из контекста → COMMIT при успехе, ROLLBACK при ошибке
    """
    uow = SqlAlchemyUnitOfWork(async_session_maker)
    async with uow:  # BEGIN
        yield uow
    # AUTO COMMIT при успехе, ROLLBACK при ошибке

# Основной алиас,
# будем использовать в app/api/v1/dependencies.py для Use Cases и роутеров
UOWDep = Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)]
```

**Пример фабрики Use Case:**

```python
# api/v1/dependencies.py
from app.use_cases.auth.register import RegisterUserUseCase

def get_register_use_case(uow: UOWDep) -> RegisterUserUseCase:
    """Создать RegisterUserUseCase с внедренным UoW."""
    return RegisterUserUseCase(uow)

# Аннотация для удобства
GetRegisterUseCaseDep = Annotated[RegisterUserUseCase, Depends(get_register_use_case)]
```

**Пример роутера с DI:**

```python
# api/v1/routers/auth.py
from app.api.v1.dependencies import GetRegisterUseCaseDep
from app.use_cases.auth.register import RegisterUserDTO

@router.post("/register/", response_model=RegisterResponse, status_code=201)
async def register(
    request: RegisterRequest,
    register_use_case: GetRegisterUseCaseDep,  # ← DI через Depends
) -> RegisterResponse:
    """Регистрация нового пользователя."""

    # 1. Pydantic схема → DTO
    dto = RegisterUserDTO(**request.model_dump())

    # 2. Выполнение Use Case (транзакция УЖЕ открыта через get_uow)
    user = await register_use_case.execute(dto)

    # 3. Domain Entity → Pydantic схема
    return RegisterResponse.model_validate(user)
```

**Пример exception handler:**

```python
# api/exception_handlers.py
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    """Преобразование доменных исключений в HTTP-ответы."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
```

**Поток данных (Регистрация пользователя):**

```
1. HTTP Request (POST /api/v1/auth/register/)
   {username, email, password}
   ↓
2. API Router (auth.py)
   ├─ RegisterRequest (Pydantic) валидирует формат JSON
   └─ Преобразует в RegisterUserDTO
   ↓
3. RegisterUserUseCase.execute(dto)
   ├─ Password VO валидирует сложность пароля (мин. 8 символов, заглавная, строчная, цифра)
   ├─ Проверяет бизнес-правила (username/email не заняты)
   ├─ User.create() создает доменную сущность
   ├─ Хеширует пароль через Argon2
   └─ uow.users.create_user(user)
   ↓
4. UserRepository (Infrastructure)
   ├─ UserMapper.to_orm(user) → UserORM
   └─ session.add(user_orm)  (БЕЗ commit!)
   ↓
5. UoW.__aexit__() автоматически делает COMMIT
   ↓
6. Use Case возвращает User (Domain Entity)
   ↓
7. Router преобразует User → RegisterResponse (Pydantic)
   ↓
8. HTTP Response (JSON 201 Created)
   {id, username, email, disabled, is_email_verified, created_at, updated_at}
```

---

### 🔵 4. Application Layer (Слой приложения)

**Папка:** [app/use_cases/](app/use_cases/)

**Назначение:** Оркестрация бизнес-логики через Use Cases. Координирует работу доменных сущностей, репозиториев и бизнес-правил.

**Состав:**

- **base.py** — BaseUseCase (базовый класс для всех Use Cases)
  - НЕ управляет транзакциями (это делает UoW через yield)
  - Обрабатывает исключения и логирование
- **auth/** — Use Cases для аутентификации
  - [register.py](app/use_cases/auth/register.py) — RegisterUserUseCase + RegisterUserDTO
  - [authenticate.py](app/use_cases/auth/authenticate.py) — AuthenticateUserUseCase
- **profile/** — Use Cases для управления профилем
  - [get.py](app/use_cases/profile/get.py) — GetUserUseCase
  - [update.py](app/use_cases/profile/update.py) — UpdateUserUseCase + UpdateUserDTO
  - [access.py](app/use_cases/profile/access.py) — DisableUserUseCase, EnableUserUseCase

**Ключевые принципы:**

- ✅ **Зависит от Domain Layer** (использует Entity, Value Objects, интерфейсы)
- ✅ **НЕ зависит** от Infrastructure (работает через интерфейсы)
- ✅ **НЕ управляет транзакциями** (это делает UoW через yield в dependencies)
- ✅ **Оркеструет** бизнес-логику через репозитории и Entity
- ✅ **DTO Pattern** — принимает frozen dataclass как входные данные
- ✅ **Один Use Case = одна бизнес-операция**
- ✅ Легко тестируется с моками

**Пример Use Case:**

```python
# use_cases/auth/register.py
from app.domain.entities.user import User
from app.domain.value_objects.password import Password
from app.domain.interfaces.unit_of_work import IUnitOfWork
from app.use_cases.base import BaseUseCase

@dataclass(frozen=True)
class RegisterUserDTO:
    """DTO для регистрации пользователя."""
    username: str
    email: str
    password: str

class RegisterUserUseCase(BaseUseCase):
    """Use Case для регистрации нового пользователя."""

    async def _run(self, dto: RegisterUserDTO) -> User:
        # 1. Проверка бизнес-правил
        if await self.uow.users.get_by_username(dto.username):
            raise UsernameAlreadyExists()

        if await self.uow.users.get_by_email(dto.email):
            raise EmailAlreadyExists()

        # 2. Валидация пароля через Value Object
        password = Password(dto.password)

        # 3. Создание доменной сущности
        new_user = User.create(username=dto.username, email=dto.email)

        # 4. Хеширование и сохранение
        hashed = get_password_hash(password.value)
        new_user.set_password(hashed)

        await self.uow.users.create_user(new_user)

        return new_user
```

---

### 🔴 5. Core Layer (Ядро)

**Папка:** `app/core/`

**Назначение:** Общие настройки, конфигурация, технические исключения.

**Состав:**

- **config.py** — настройки приложения (читает `.env`)
  - DATABASE_URL, SECRET_KEY, LOG_LEVEL, ENVIRONMENT, и т.д.
- **dependencies.py** — глобальные зависимости (например, создание DB Session)
- **exceptions/** — технические исключения
  - `auth.py` — InvalidToken, InvalidCredentials (не бизнес-логика!)
  - `base.py` — AppError (базовое техническое исключение)
  - `messages.py` — сообщения об ошибках

**Принципы:**

- ✅ Не зависит от domain
- ✅ Содержит технические (не доменные) исключения
- ✅ Конфигурация для всех слоёв

**Пример:**

```python
# core/config.py
class Settings(BaseSettings):
    APP_NAME: str = "UseCase API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    SECRET_KEY: str
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

### 🟣 6. Shared Layer (Общие утилиты)

**Папка:** `app/shared/`

**Назначение:** Переиспользуемый код, не относящийся к конкретному слою.

**Состав:**

- **logging.py** — настройка структурированного логирования (JSON/Text)
  - Correlation ID для трассировки запросов
  - Ротация логов по дням

**Принципы:**

- ✅ Не зависит от других слоёв
- ✅ Переиспользуемые утилиты

**Пример:**

```python
# shared/logging.py
def setup_logging():
    """Настройка логирования с поддержкой JSON-формата."""
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
```

---

## Технологический стек

### Backend

- **FastAPI 0.128.8** — современный веб-фреймворк для асинхронных REST API
- **SQLAlchemy 2.0.46** — async ORM для работы с PostgreSQL
- **asyncpg 0.30.0** — асинхронный драйвер PostgreSQL
- **Alembic 1.18.4** — миграции базы данных
- **Pydantic 2.12.5** — валидация данных и схемы
- **PyJWT 2.11.0** — генерация и валидация JWT-токенов
- **pwdlib 0.2.3** + **Argon2** — современное хеширование паролей

### База данных

- **PostgreSQL 16.2** — реляционная БД в Docker контейнере

### Инфраструктура

- **Docker** + **Docker Compose** — контейнеризация PostgreSQL
- **Poetry 1.8+** — управление зависимостями Python
- **Makefile** — автоматизация команд разработки

### Инструменты разработки

- **Ruff** — быстрый линтер и форматтер Python кода
- **Python 3.12+** — современные type hints, dataclasses

---

## Установка и запуск

### Предварительные требования

- **Python 3.12+** — для современных type hints и dataclasses
- **Docker** и **Docker Compose** — для запуска PostgreSQL
- **Poetry 1.8+** — для управления зависимостями (рекомендуется)

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Base-Project
```

### 2. Создание .env файла

```bash
# Скопируйте пример и настройте
cp .env.example .env
```

**Пример .env файла:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://admin:admin1234@localhost:5433/db

# Security
SECRET_KEY=your-secret-key-change-this-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_NAME=Base APP
ENVIRONMENT=dev
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Запуск PostgreSQL в Docker

```bash
# Запустить БД в фоне
docker compose up -d

# Проверить статус
docker compose ps

# Посмотреть логи
docker compose logs -f postgres
```

### 4. Установка зависимостей

**С Poetry (рекомендуется):**

```bash
# Установить Poetry, если еще не установлен
curl -sSL https://install.python-poetry.org | python3 -

# Установить зависимости
poetry install

# Активировать виртуальное окружение
poetry shell
```

**Или с pip:**

```bash
# Создать виртуальное окружение
python3.12 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
# или
pip install \
  "fastapi>=0.128.8,<0.129.0" \
  "uvicorn[standard]>=0.40.0,<0.41.0" \
  "pwdlib[argon2]>=0.3.0,<0.4.0" \
  "pyjwt>=2.11.0,<3.0.0" \
  "sqlalchemy[asyncio]>=2.0.46,<3.0.0" \
  "asyncpg>=0.31.0,<0.32.0" \
  "alembic>=1.18.4,<2.0.0" \
  "pydantic-settings>=2.12.0,<3.0.0" \
  "pydantic[email]>=2.12.5,<3.0.0" \
  "python-multipart>=0.0.22,<0.0.23"

```

### 5. Применение миграций Alembic

```bash
# С Makefile
make migrate

# Или напрямую через Alembic
alembic upgrade head

# Создать новую миграцию (если нужно)
alembic revision --autogenerate -m "описание изменений"
```

### 6. Запуск приложения

```bash
# С Makefile
make run

# Или напрямую с Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или с активированным venv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Проверка работы

Откройте в браузере:

- **Swagger UI (интерактивная документация):** http://localhost:8000/docs
- **ReDoc (альтернативная документация):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/v1/healthcheck

---

## Makefile команды

```bash
# Запустить приложение
make run

# Проверить код линтером
make lint

# Только форматирование
make fmt

# Проверка кода без исправлений
make check

# Автоисправление и форматирование
make fix
```

---

## Работа с миграциями

### Применить существующие миграции (стандартный сценарий)

Миграции уже находятся в проекте и готовы к использованию:

```bash
# С Makefile
make migrate

# Или напрямую через Alembic
alembic upgrade head
```

### Создать миграции заново (для обучения/экспериментов)

Если вы хотите пересоздать миграции с нуля для изучения процесса:

```bash
# 1. Удалить существующие миграции
rm migrations/versions/*.py

# 2. Создать новую миграцию на основе моделей
alembic revision --autogenerate -m "initial migration"

# 3. Применить миграцию
alembic upgrade head
```

### Полезные команды Alembic

```bash
# Посмотреть текущую версию БД
alembic current

# Посмотреть историю миграций
alembic history

# Откатить на одну миграцию назад
alembic downgrade -1

# Откатить до конкретной версии
alembic downgrade <revision_id>

# Создать пустую миграцию (для ручных изменений)
alembic revision -m "описание изменений"
```

### Почему миграции в git?

В этом проекте миграции включены в git, что является **стандартной практикой** в production:

- ✅ Воспроизводимая схема БД для всех разработчиков
- ✅ История изменений структуры БД
- ✅ Простое развертывание (скачал → применил миграции → готово)
- ✅ Соответствует реальным проектам

Вы можете удалить и пересоздать миграции для обучения — это не сломает проект.

---

## API документация

### Основные эндпоинты

#### Аутентификация

**POST /api/v1/auth/register/**

Регистрация нового пользователя с валидацией пароля через Password Value Object.

```json
// Request
{
  "username": "john_doe",              // минимум 4 символа
  "email": "john@example.com",         // валидный email
  "password": "SecurePass123"          // минимум 8 символов, заглавная буква, строчная буква, цифра
}

// Response (201 Created)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "disabled": false,
  "is_email_verified": false,
  "created_at": "2025-02-18T10:30:00Z",
  "updated_at": "2025-02-18T10:30:00Z"
}

// Error (400 Bad Request) - слабый пароль
{
  "detail": "Пароль должен содержать заглавную букву"
}
```

**Требования к паролю (Password VO):**

- Минимум 8 символов
- Минимум одна заглавная буква (A-Z)
- Минимум одна строчная буква (a-z)
- Минимум одна цифра (0-9)

**POST /api/v1/auth/login/**

Вход в систему, получение JWT-токена.

```json
// Request
{
  "username": "john_doe",
  "password": "SecurePass123"
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

// Error (401 Unauthorized) - неверные учетные данные
{
  "detail": "Неверное имя пользователя или пароль"
}
```

#### Пользователи

**GET /api/v1/users/me/**

Получение информации о текущем аутентифицированном пользователе.

```bash
# Требует Bearer token в заголовке Authorization
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/users/me/

# Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "disabled": false,
  "is_email_verified": false,
  "created_at": "2025-02-18T10:30:00Z",
  "updated_at": "2025-02-18T10:30:00Z"
}
```

**PATCH /api/v1/users/me/**

Обновление профиля текущего пользователя.

```json
// Request
{
  "current_password": "SecurePass123",      // обязательно для подтверждения
  "username": "john_new",                   // опционально
  "email": "new_email@example.com",         // опционально
  "new_password": "NewSecurePass456"        // опционально, валидация через Password VO
}

// Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_new",
  "email": "new_email@example.com",
  "disabled": false,
  "is_email_verified": false,  // сбрасывается при смене email
  "created_at": "2025-02-18T10:30:00Z",
  "updated_at": "2025-02-18T12:45:00Z"
}
```

### Health Check

**GET /api/v1/healthcheck**

```json
{
  "status": "healthy",
  "timestamp": "2025-02-18T10:30:00Z"
}
```

### Интерактивная документация

- **Swagger UI (интерактивное тестирование):** http://localhost:8000/docs
- **ReDoc (читаемая документация):** http://localhost:8000/redoc

---

## Дополнительная документация

- **[app/domain/README.md](app/domain/README.md)** — документация доменного слоя
- **[app/domain/EXAMPLES.py](app/domain/EXAMPLES.py)** — примеры использования domain

---

## Особенности проекта

### ✅ Clean Architecture + DDD

- **Инверсия зависимостей**: зависимости направлены от Infrastructure к Domain
- **Domain Layer** не знает о БД, API, фреймворках
- **Value Objects** для валидации данных (Password, UserIdentity, UserSecurity)
- **Domain Entities** с бизнес-методами (disable, change_email, и т.д.)
- Легко тестируется и расширяется

### ✅ Unit of Work Pattern с Yield

- **Транзакции управляются** через `get_uow()` с `yield` в dependencies
- **Одна транзакция** на весь HTTP-запрос
- **UoW.**aexit**()** автоматически делает COMMIT при успехе, ROLLBACK при ошибке
- **Use Cases НЕ управляют** транзакциями (только бизнес-логика)
- Все репозитории используют **одну и ту же сессию**

### ✅ Use Cases организованы по доменам

- Бизнес-логика инкапсулирована в Use Cases
- Организация по bounded contexts: `auth/` (аутентификация), `profile/` (профиль)
- Один Use Case = одна бизнес-операция
- **DTO Pattern** — Use Cases принимают frozen dataclass
- Прозрачная оркестрация репозиториев через UoW

### ✅ Mapper Pattern

- **UserMapper** изолирует Domain от Infrastructure
- Преобразования: `to_domain()`, `to_orm()`, `update_orm_from_domain()`
- Domain работает с **User Entity**, Infrastructure — с **UserORM**
- Можно заменить БД без изменения Domain

### ✅ Value Objects с валидацией

- **Password VO** — валидация сложности пароля ДО хеширования
- **UserIdentity VO** — username + email с валидацией
- **UserSecurity VO** — hashed_password + disabled + is_email_verified
- Неизменяемые (`frozen=True`), сравниваются по значению

### ✅ "Худые" контроллеры

- Контроллеры не знают о репозиториях
- Контроллеры не управляют транзакциями
- Только: Pydantic схема → DTO → Use Case → Domain Entity → Pydantic схема
- Пример: `return RegisterResponse.model_validate(user)`

### ✅ Dependency Injection

- FastAPI `Depends()` для DI
- Фабрики Use Cases с аннотациями (`GetRegisterUseCaseDep`)
- Легко подменять зависимости в тестах (моки)
- Чистый и читаемый код без глобальных переменных

### ✅ Структурированное логирование

- JSON или текстовый формат (настраивается через .env)
- **Correlation ID** для трассировки запросов через `contextvars`
- Ротация логов по дням
- Логирование бизнес-операций в Use Cases

### ✅ Современный стек безопасности

- **PyJWT** для генерации и валидации JWT-токенов
- **pwdlib + Argon2** для хеширования паролей (вместо устаревшего bcrypt)
- Password Value Object для валидации сложности
- Проверка `disabled` и `is_email_verified` при аутентификации

### ✅ Типизация

- Полная типизация Python 3.12+ с современными type hints
- Pydantic 2.12 для валидации данных
- Type hints для Domain Entities, Use Cases, репозиториев
- Поддержка `|` для Optional типов

### ✅ Миграции Alembic

- Версионирование схемы БД
- Автоматическая генерация миграций (`alembic revision --autogenerate`)
- Откат и накат версий (`upgrade`, `downgrade`)
- Timezone-aware datetime для всех временных полей

---

## Roadmap

- [ ] Добавить unit-тесты для domain layer
- [ ] Добавить integration тесты для API
- [ ] Добавить Docker образ для production
- [ ] Добавить CI/CD (GitHub Actions)
- [ ] Добавить метрики (Prometheus)
- [ ] Добавить трейсинг (OpenTelemetry)
- [ ] Добавить rate limiting
- [ ] Добавить кэширование (Redis)

---

## Лицензия

MIT

---

## Автор

[Александр Терехов](https://stepik.org/a/223717)

---

## Благодарности

- **Robert C. Martin** — за Clean Architecture
- **Eric Evans** — за Domain-Driven Design
- **FastAPI** community
