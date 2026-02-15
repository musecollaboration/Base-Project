# Domain Layer (Доменный слой приложения)

## Назначение

Domain Layer — это **ядро приложения**, содержащее бизнес-логику, правила и модели предметной области. Он полностью **независим от внешних систем** (БД, API, фреймворков) и определяет **ЧТО делает** приложение, но не **КАК** это реализовано.

**Ключевой принцип:** Domain Layer — самый важный слой, от которого зависят все остальные. Он сам НИ ОТ КОГО не зависит.

---

## Структура

```
domain/
├── __init__.py                   # Экспорты доменного слоя
├── entities/                     # 🔵 Доменные сущности
│   ├── __init__.py
│   └── user.py                   # User + UserIdentity + UserSecurity (Value Objects)
├── exceptions/                   # Доменные исключения
│   ├── __init__.py
│   ├── base.py                   # DomainException (базовый класс)
│   ├── messages.py               # Сообщения бизнес-ошибок
│   └── users.py                  # UserNotFound, EmailAlreadyExists, и т.д.
├── interfaces/                   # 🟢 Абстрактные интерфейсы (порты)
│   ├── __init__.py
│   ├── unit_of_work.py           # IUnitOfWork (ABC)
│   └── user_repository.py        # UserRepository (ABC)
├── value_objects/                # 🟡 Value Objects (неизменяемые объекты-значения)
│   ├── __init__.py
│   ├── email.py                  # Email VO (не используется напрямую)
│   └── password.py               # Password VO с валидацией сложности
├── EXAMPLES.py                   # Примеры использования Domain Layer
└── README.md                     # Данный файл
```

---

## Компоненты Domain Layer

**Примечание:** Use Cases вынесены в отдельную папку `app/use_cases/` (см. Application Layer).

### 1. 🔵 Entities (Доменные сущности)

**Файл:** [entities/user.py](entities/user.py)

**Что это:** Объекты с уникальной идентичностью, содержащие бизнес-логику и методы.

#### User Entity

```python
class User:
    """
    Доменная сущность пользователя.

    Композирует Value Objects:
    - UserIdentity (username, email)
    - UserSecurity (hashed_password, disabled, is_email_verified)
    """

    def __init__(
        self,
        id: UUID,
        identity: UserIdentity,    # Value Object
        security: UserSecurity,    # Value Object
        created_at: datetime,
        updated_at: datetime,
    ):
        self._id = id
        self._identity = identity
        self._security = security
        self._created_at = created_at
        self._updated_at = updated_at

    # Properties (доступ к внутреннему состоянию)
    @property
    def id(self) -> UUID:
        return self._id

    @property
    def username(self) -> str:
        return self._identity.username

    @property
    def email(self) -> str:
        return self._identity.email

    # Бизнес-методы
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
        # Создаем новый Identity (VO неизменяемы)
        self._identity = UserIdentity(username=self.username, email=new_email)
        # Сбрасываем верификацию
        self._security = replace(self._security, is_email_verified=False)
        self._updated_at = datetime.now(timezone.utc)
```

**Принципы Entity:**

- ✅ Имеет уникальный ID
- ✅ Содержит бизнес-методы (`disable()`, `change_email()`)
- ✅ Валидирует данные через Value Objects
- ✅ Не знает о БД, API, фреймворках
- ✅ Использует фабричные методы для создания (`create()`)

---

### 2. 🟡 Value Objects (Объекты-значения)

**Папка:** [value_objects/](value_objects/)

**Что это:** Неизменяемые объекты без идентичности, сравниваемые по значению. Содержат валидацию.

#### 2.1 Password Value Object

**Файл:** [value_objects/password.py](value_objects/password.py)

```python
@dataclass(frozen=True)
class Password:
    """
    Value Object для plaintext пароля с валидацией сложности.

    Валидирует ДО хеширования!
    """
    value: str

    def __post_init__(self):
        # Минимум 8 символов
        if len(self.value) < 8:
            raise InvalidPasswordFormat("Пароль должен быть минимум 8 символов")

        # Заглавная буква
        if not re.search(r'[A-Z]', self.value):
            raise InvalidPasswordFormat("Пароль должен содержать заглавную букву")

        # Строчная буква
        if not re.search(r'[a-z]', self.value):
            raise InvalidPasswordFormat("Пароль должен содержать строчную букву")

        # Цифра
        if not re.search(r'[0-9]', self.value):
            raise InvalidPasswordFormat("Пароль должен содержать цифру")
```

**Использование Password:**

```python
# В Use Case
async def _run(self, dto: RegisterUserDTO) -> User:
    # Валидация plaintext пароля ПЕРЕД хешированием
    password = Password(dto.password)  # ← Валидация здесь!

    # Хеширование валидного пароля
    hashed = get_password_hash(password.value)
    user.set_password(hashed)
```

#### 2.2 UserIdentity Value Object

**Находится в:** [entities/user.py](entities/user.py)

```python
@dataclass(frozen=True)
class UserIdentity:
    """Value Object для данных идентификации пользователя."""
    username: str
    email: str

    def __post_init__(self):
        # Валидация username
        if not self.username or len(self.username) < 4:
            raise InvalidUsernameFormat()

        # Валидация email
        if "@" not in self.email:
            raise InvalidEmailFormat()
```

#### 2.3 UserSecurity Value Object

**Находится в:** [entities/user.py](entities/user.py)

```python
@dataclass(frozen=True)
class UserSecurity:
    """Value Object для данных безопасности."""
    hashed_password: str = ""
    disabled: bool = False
    is_email_verified: bool = False
```

**Принципы Value Objects:**

- ✅ Неизменяемые (`frozen=True`)
- ✅ Сравниваются по значению
- ✅ Содержат валидацию в `__post_init__`
- ✅ Используются для композиции в Entity

---

### 3. 🟢 Interfaces (Интерфейсы)

**Папка:** [interfaces/](interfaces/)

**Что это:** Абстрактные интерфейсы (порты), определяющие контракт для внешних систем.

#### 4.1 UserRepository Interface

**Файл:** [interfaces/user_repository.py](interfaces/user_repository.py)

```python
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities.user import User

class UserRepository(ABC):
    """Абстрактный интерфейс репозитория пользователей."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить пользователя по ID."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Получить пользователя по username."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Получить пользователя по email."""
        ...

    @abstractmethod
    async def create_user(self, user: User) -> None:
        """Создать нового пользователя."""
        ...

    @abstractmethod
    async def update_user(self, user: User) -> None:
        """Обновить существующего пользователя."""
        ...
```

**Ключевое изменение:** Репозиторий работает с **Domain Entity** (User), а не с ORM моделями!

#### 4.2 IUnitOfWork Interface

**Файл:** [interfaces/unit_of_work.py](interfaces/unit_of_work.py)

```python
from abc import ABC, abstractmethod
from app.domain.interfaces.user_repository import UserRepository

class IUnitOfWork(ABC):
    """
    Интерфейс Unit of Work.

    Гарантирует, что все репозитории используют одну транзакцию.
    """

    users: UserRepository
    # Здесь будут другие репозитории по мере добавления

    @abstractmethod
    async def __aenter__(self):
        """Вход в контекстный менеджер (BEGIN транзакции)."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера (COMMIT или ROLLBACK)."""
        ...

    @abstractmethod
    async def commit(self):
        """Зафиксировать транзакцию."""
        ...

    @abstractmethod
    async def rollback(self):
        """Откатить транзакцию."""
        ...
```

**Принципы Interfaces:**

- ✅ Определяют **ЧТО** нужно сделать, но не **КАК**
- ✅ Реализуются в Infrastructure Layer
- ✅ Позволяют менять реализацию без изменения Domain
- ✅ Инверсия зависимостей (DIP из SOLID)

---

### 4. 🔴 Exceptions (Доменные исключения)

**Папка:** [exceptions/](exceptions/)

**Что это:** Исключения, связанные с нарушением бизнес-правил.

#### 5.1 DomainException (базовый класс)

**Файл:** [exceptions/base.py](exceptions/base.py)

```python
class DomainException(Exception):
    """Базовое исключение для всего домена."""

    message: str = "Произошла ошибка бизнес-логики"
    status_code: int = 400

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)
```

#### 5.2 Конкретные доменные исключения

**Файл:** [exceptions/users.py](exceptions/users.py)

```python
class UserNotFound(DomainException):
    """Пользователь не найден."""
    message = "Пользователь не найден"
    status_code = 404

class EmailAlreadyExists(DomainException):
    """Email уже используется."""
    message = "Пользователь с таким email уже существует"
    status_code = 409

class UsernameAlreadyExists(DomainException):
    """Username уже используется."""
    message = "Пользователь с таким именем уже существует"
    status_code = 409

class InvalidPasswordFormat(DomainException):
    """Пароль не соответствует требованиям."""
    message = "Пароль слишком слабый или короткий"
    status_code = 400

class InvalidPasswordException(DomainException):
    """Текущий пароль указан неверно."""
    message = "Текущий пароль указан неверно"
    status_code = 403

class EmailNotVerified(DomainException):
    """Email не подтвержден."""
    message = "Пожалуйста, подтвердите ваш email перед входом"
    status_code = 403
```

**Разделение исключений:**

| Тип             | Где находится        | Примеры                          |
| --------------- | -------------------- | -------------------------------- |
| **Доменные**    | `domain/exceptions/` | UserNotFound, EmailAlreadyExists |
| **Технические** | `core/exceptions/`   | InvalidToken, AuthUserNotFound   |

**Принципы Exceptions:**

- ✅ Наследуются от DomainException
- ✅ Содержат message и status_code
- ✅ Преобразуются в HTTP-ответы в exception_handlers.py
- ✅ Отражают нарушение бизнес-правил

---

## Использование Domain Layer

### В API Dependencies

**Файл:** `app/api/v1/dependencies.py`

```python
from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.use_cases.auth.register import RegisterUserUseCase

# UoW с yield (управление транзакциями)
async def get_uow():
    """Unit of Work с автоматическим управлением транзакциями."""
    uow = SqlAlchemyUnitOfWork(async_session_maker)
    async with uow:  # BEGIN
        yield uow
    # AUTO COMMIT при успехе, ROLLBACK при ошибке

# Фабрики Use Cases
def get_register_use_case(uow: SqlAlchemyUnitOfWork = Depends(get_uow)) -> RegisterUserUseCase:
    return RegisterUserUseCase(uow)

# Аннотации для роутеров
GetRegisterUseCaseDep = Annotated[RegisterUserUseCase, Depends(get_register_use_case)]
```

### В API Routers

**Файл:** `app/api/v1/routers/auth.py`

```python
from app.api.v1.dependencies import GetRegisterUseCaseDep
from app.use_cases.auth.register import RegisterUserDTO

@router.post("/register/", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    register_use_case: GetRegisterUseCaseDep,  # ← DI через Depends
) -> RegisterResponse:
    """Регистрация пользователя."""

    # 1. Pydantic схема → DTO
    dto = RegisterUserDTO(**request.model_dump())

    # 2. Выполнение Use Case
    user = await register_use_case.execute(dto)

    # 3. Domain Entity → Pydantic схема
    return RegisterResponse.model_validate(user)
```

---

## Поток данных (Data Flow)

### Регистрация пользователя

```
1. HTTP Request (POST /api/v1/auth/register/)
   {username, email, password}
   ↓
2. API Router (auth.py)
   ├─ RegisterRequest (Pydantic) валидирует формат
   └─ Преобразует в RegisterUserDTO
   ↓
3. RegisterUserUseCase.execute(dto)
   ├─ Password VO валидирует сложность пароля
   ├─ Проверяет бизнес-правила (username/email не заняты)
   ├─ User.create() создает доменную сущность
   ├─ Хеширует пароль
   └─ uow.users.create_user(user)
   ↓
4. UserRepository (Infrastructure)
   ├─ UserMapper.to_orm(user) → UserORM
   └─ session.add(user_orm)
   ↓
5. UoW.__aexit__() автоматически делает COMMIT
   ↓
6. Use Case возвращает User (Domain Entity)
   ↓
7. Router преобразует User → RegisterResponse (Pydantic)
   ↓
8. HTTP Response (JSON)
   {id, username, email, disabled, is_email_verified, ...}
```

### Направление зависимостей

```
┌──────────────────────────────────────┐
│      Presentation Layer              │
│   (api/routers, schemas)             │
└────────────┬─────────────────────────┘
             │ зависит от
             ↓
┌──────────────────────────────────────┐
│       Application Layer              │
│       (use_cases)                    │
└────────────┬─────────────────────────┘
             │ зависит от
             ↓
┌──────────────────────────────────────┐
│          Domain Layer                │
│  (entities, interfaces, exceptions)  │
└────────────┬─────────────────────────┘
             ↑ реализует
             │
┌──────────────────────────────────────┐
│      Infrastructure Layer            │
│  (repositories, database, mappers)   │
└──────────────────────────────────────┘
```

**Ключевой принцип:** Domain НЕ зависит ни от кого!

---

## Принципы Clean Architecture в Domain Layer

### 1. Независимость от фреймворков

Domain не использует FastAPI, SQLAlchemy, Pydantic напрямую.

✅ **Правильно:**

```python
# domain/entities/user.py
class User:
    def __init__(self, id: UUID, identity: UserIdentity, ...):
        self._id = id
        self._identity = identity
```

❌ **Неправильно:**

```python
# НЕ В DOMAIN!
from pydantic import BaseModel

class User(BaseModel):  # ❌ Зависимость от Pydantic
    username: str
```

### 2. Тестируемость

Бизнес-логику можно тестировать БЕЗ БД, HTTP, внешних сервисов.

```python
def test_user_disable():
    """Тест доменной логики без БД."""
    user = User.create(username="test", email="test@test.com")

    assert user.is_enabled is True

    user.disable()

    assert user.is_enabled is False
    assert user.disabled is True
```

### 3. Независимость от БД

Можно заменить PostgreSQL на MongoDB без изменения Domain.

```python
# domain/interfaces/user_repository.py — НЕ МЕНЯЕТСЯ
class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

# infrastructure/repositories/user.py — РЕАЛИЗАЦИЯ МЕНЯЕТСЯ
class UserRepository(UserRepositoryInterface):
    # Postgres / MongoDB / Redis - любая реализация
    pass
```

### 4. Бизнес-логика в одном месте

Вся логика инкапсулирована в Domain, не размазана по коду.

✅ **Правильно:**

```python
# use_cases/auth/register.py
class RegisterUserUseCase:
    async def _run(self, dto: RegisterUserDTO) -> User:
        # Вся бизнес-логика регистрации здесь
        password = Password(dto.password)  # Валидация
        if await self.uow.users.get_by_username(dto.username):
            raise UsernameAlreadyExists()
        # ...
```

❌ **Неправильно:**

```python
# api/routers/auth.py
@router.post("/register/")
async def register(request: RegisterRequest, db: Session):
    # ❌ Бизнес-логика в контроллере!
    if db.query(User).filter_by(username=request.username).first():
        raise HTTPException(409, "User exists")
    # ...
```

---

## Чек-лист правильного Domain Layer

- ✅ Entities содержат бизнес-методы
- ✅ Value Objects валидируют данные
- ✅ Use Cases принимают DTO
- ✅ Use Cases работают через UoW
- ✅ Интерфейсы определяют контракт
- ✅ Доменные исключения наследуются от DomainException
- ✅ Mapper изолирует Domain от Infrastructure
- ✅ НЕТ импортов из infrastructure, api, core
- ✅ Domain можно тестировать без БД
- ✅ Бизнес-правила проверяются в Use Cases

---

## Дополнительная информация

- **Примеры использования:** [EXAMPLES.py](EXAMPLES.py)
- **Корневой README:** [../../README.md](../../README.md)

---

**Цель Domain Layer:** Быть независимым, тестируемым ядром бизнес-логики, которое можно переиспользовать в любом контексте (CLI, GUI, другой API, микросервисы).
