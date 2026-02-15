"""
Примеры использования Domain Layer (Clean Architecture + DDD).

Этот файл демонстрирует правильное применение паттернов:
- Unit of Work
- Use Cases с DTO
- Value Objects (Password, UserIdentity, UserSecurity)
- Repositories через интерфейсы
- Mapper Pattern
- Dependency Injection
"""

from unittest.mock import AsyncMock
from uuid import UUID

from app.domain.entities.user import User, UserIdentity, UserSecurity
from app.domain.interfaces.unit_of_work import IUnitOfWork
from app.domain.interfaces.user_repository import UserRepository
from app.use_cases.auth.authenticate import AuthenticateUserUseCase
from app.use_cases.auth.register import RegisterUserDTO, RegisterUserUseCase
from app.use_cases.profile.access import DisableUserUseCase, EnableUserUseCase
from app.use_cases.profile.get import GetUserUseCase
from app.use_cases.profile.update import UpdateUserDTO, UpdateUserUseCase
from app.domain.value_objects.password import Password

# =====================================================
# Пример 1: Регистрация пользователя через Use Case + DTO
# =====================================================


async def register_user_example(uow: IUnitOfWork):
    """
    Пример регистрации пользователя через RegisterUserUseCase.

    ✅ Правильно: используем DTO и UoW
    """
    use_case = RegisterUserUseCase(uow)

    # Создаем DTO для передачи данных
    dto = RegisterUserDTO(
        username="john_doe",  # минимум 4 символа
        email="john@example.com",
        password="SecurePass123",  # валидация через Password VO
    )

    # Execute возвращает Domain Entity
    user = await use_case.execute(dto)

    print(f"Пользователь создан: {user.username}, ID: {user.id}")
    return user


# =====================================================
# Пример 2: Аутентификация пользователя
# =====================================================


async def authenticate_user_example(uow: IUnitOfWork):
    """
    Пример аутентификации через AuthenticateUserUseCase.

    Возвращает JWT токен.
    """
    use_case = AuthenticateUserUseCase(uow)

    result = await use_case.execute(username="john_doe", password="SecurePass123")

    # result = {"access_token": "...", "token_type": "bearer"}
    print(f"Токен создан: {result['access_token']}")
    return result


# =====================================================
# Пример 3: Обновление профиля пользователя
# =====================================================


async def update_user_profile_example(uow: IUnitOfWork, user: User):
    """
    Пример обновления профиля через UpdateUserUseCase + DTO.

    ✅ Password валидируется через Password VO
    """
    use_case = UpdateUserUseCase(uow)

    # Создаем DTO с новыми данными
    dto = UpdateUserDTO(
        current_password="SecurePass123",
        username="john_updated",
        email="john_new@example.com",
        new_password="NewSecure456",  # Валидация в Use Case через Password VO
    )

    # Execute обновляет user и возвращает обновленную сущность
    updated_user = await use_case.execute(user, dto)

    print(f"Профиль обновлен: {updated_user.username}, {updated_user.email}")
    return updated_user


# =====================================================
# Пример 4: Работа с Value Objects
# =====================================================


async def value_objects_example():
    """
    Пример использования Value Objects.

    Value Objects валидируют данные при создании.
    """
    # Password Value Object - валидация сложности
    try:
        _ = Password("123")  # ❌ Слишком короткий
    except Exception as e:
        print(f"Ошибка валидации пароля: {e}")

    # ✅ Правильный пароль
    strong_password = Password("SecurePass123")
    print(f"Пароль валиден: {strong_password.value}")

    # UserIdentity Value Object - валидация username и email
    try:
        identity = UserIdentity(
            # ❌ Слишком короткий (минимум 4)
            username="abc",
            email="test@test.com",
        )
    except Exception as e:
        print(f"Ошибка валидации identity: {e}")

    # ✅ Правильный Identity
    identity = UserIdentity(username="john_doe", email="john@example.com")
    print(f"Identity валиден: {identity.username}, {identity.email}")

    # UserSecurity Value Object - композиция в User
    security = UserSecurity(
        hashed_password="$argon2id$...", disabled=False, is_email_verified=True
    )
    print(f"Security создан: disabled={security.disabled}")


# =====================================================
# Пример 5: Работа с маппером (Domain ↔ Infrastructure)
# =====================================================


async def mapper_example(user_repo: UserRepository, user_id: UUID):
    """
    Пример использования UserMapper для преобразования.

    ORM ↔ Domain Entity
    """
    # Получаем пользователя из репозитория (возвращает Domain Entity)
    user = await user_repo.get_by_id(user_id)

    if not user:
        print("Пользователь не найден")
        return

    # Работаем с доменной сущностью
    user.change_email("new_email@example.com")

    # Сохраняем через репозиторий (mapper внутри)
    await user_repo.update_user(user)

    print(f"Email обновлен: {user.email}")
    return user


# =====================================================
# Пример 6: Unit of Work паттерн
# =====================================================


async def unit_of_work_example():
    """
    Пример использования Unit of Work.

    ✅ UoW управляет транзакциями автоматически через yield в dependencies.
    """
    from app.infrastructure.database.engine import async_session_maker
    from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

    # В реальном коде UoW создается через Depends(get_uow)
    # Здесь показываем ручное использование для понимания

    uow = SqlAlchemyUnitOfWork(async_session_maker)

    async with uow:  # BEGIN транзакции
        # Создаем пользователя
        dto = RegisterUserDTO(
            username="test_user", email="test@example.com", password="TestPass123"
        )
        use_case = RegisterUserUseCase(uow)
        user = await use_case._run(dto)  # Вызываем _run напрямую для примера

        # UoW автоматически сделает COMMIT при выходе из контекста
        # Или ROLLBACK если будет исключение

    print(f"Пользователь создан через UoW: {user.username}")


# =====================================================
# Пример 7: Dependency Injection в FastAPI
# =====================================================


async def fastapi_integration_example():
    """
    Пример интеграции с FastAPI через Dependency Injection.

    ⚡ Ключевой принцип: контроллер НЕ создает Use Case напрямую,
    а получает его через Depends.
    """
    from fastapi import APIRouter

    from app.api.v1.dependencies import GetCurrentUserDep, GetRegisterUseCaseDep
    from app.api.v1.schemas.auth import RegisterRequest, RegisterResponse
    from app.api.v1.schemas.user import UserResponse

    router = APIRouter()

    @router.post("/register/", response_model=RegisterResponse)
    async def register(
        request: RegisterRequest,
        register_use_case: GetRegisterUseCaseDep,  # ← DI через Depends
    ) -> RegisterResponse:
        """
        Регистрация пользователя.

        1. Pydantic схема → DTO
        2. Use Case.execute(dto)
        3. Domain Entity → Pydantic схема
        """
        dto = RegisterUserDTO(**request.model_dump())
        user_entity = await register_use_case.execute(dto)
        return RegisterResponse.model_validate(user_entity)

    @router.get("/me/", response_model=UserResponse)
    async def get_current_user(
        current_user: GetCurrentUserDep,  # ← DI возвращает User Entity
    ) -> UserResponse:
        """
        Получение текущего пользователя.

        current_user уже Domain Entity благодаря Depends.
        """
        return UserResponse.model_validate(current_user)


# =====================================================
# Пример 8: Тестирование Use Case с моком
# =====================================================


async def test_register_use_case_with_mock():
    """
    Пример unit-теста Use Case с мокированным UoW.

    ✅ Тестируем бизнес-логику БЕЗ реальной БД.
    """
    # Создаем мок UoW
    mock_uow = AsyncMock(spec=IUnitOfWork)

    # Мок репозитория внутри UoW
    mock_user_repo = AsyncMock(spec=UserRepository)
    mock_user_repo.get_by_username.return_value = None  # username свободен
    mock_user_repo.get_by_email.return_value = None  # email свободен
    mock_user_repo.create_user.return_value = None

    # Подключаем мок репозитория к UoW
    mock_uow.users = mock_user_repo

    # Тестируем Use Case
    use_case = RegisterUserUseCase(mock_uow)
    dto = RegisterUserDTO(
        username="test_user", email="test@test.com", password="TestPass123"
    )

    user = await use_case._run(dto)

    # Проверяем результат
    assert user.username == "test_user"
    assert user.email == "test@test.com"
    assert user.hashed_password != ""  # Пароль захеширован
    assert not user.disabled

    # Проверяем, что репозиторий был вызван
    mock_user_repo.create_user.assert_called_once()

    print("✅ Тест пройден!")


# =====================================================
# Пример 9: Тестирование доменной логики
# =====================================================


async def test_user_entity_methods():
    """
    Пример тестирования методов Domain Entity без БД.

    ✅ Чистая бизнес-логика, никаких зависимостей.
    """

    # Создаем пользователя через фабричный метод
    user = User.create(username="john_doe", email="john@test.com")

    # Тестируем бизнес-методы
    assert user.is_enabled is True
    assert user.is_email_verified is False

    # Деактивация
    user.disable()
    assert user.is_enabled is False

    # Активация
    user.enable()
    assert user.is_enabled is True

    # Смена email сбрасывает верификацию
    user.mark_email_as_verified()
    assert user.is_email_verified is True

    user.change_email("new@test.com")
    assert user.email == "new@test.com"
    assert user.is_email_verified is False  # ← Сброшена!

    print("✅ Все бизнес-методы работают корректно!")


# =====================================================
# Пример 10: Цепочка Use Cases в одной транзакции
# =====================================================


async def chain_use_cases_in_transaction(uow: IUnitOfWork):
    """
    Пример последовательного использования нескольких Use Cases.

    ⚡ Важно: все операции в одной транзакции благодаря UoW.
    """
    # 1. Регистрация
    register_uc = RegisterUserUseCase(uow)
    dto = RegisterUserDTO(
        username="alice", email="alice@example.com", password="AlicePass123"
    )
    user = await register_uc.execute(dto)
    print(f"1. Зарегистрирован: {user.username}")

    # 2. Получение
    get_uc = GetUserUseCase(uow)
    fetched_user = await get_uc.execute(user.id)
    print(f"2. Получен: {fetched_user.username}")

    # 3. Деактивация
    disable_uc = DisableUserUseCase(uow)
    disabled_user = await disable_uc.execute(user.id)
    print(
        f"3. Деактивирован: {disabled_user.username}, disabled={disabled_user.disabled}"
    )

    # 4. Активация
    enable_uc = EnableUserUseCase(uow)
    enabled_user = await enable_uc.execute(user.id)
    print(f"4. Активирован: {enabled_user.username}, disabled={enabled_user.disabled}")
    return enabled_user


# =====================================================
# Пример 11: Обработка доменных исключений
# =====================================================


async def handle_domain_exceptions_example(uow: IUnitOfWork):
    """
    Пример обработки доменных исключений.

    Доменные исключения преобразуются в HTTP-ответы в exception_handlers.py
    """
    from app.domain.exceptions import (
        InvalidPasswordFormat,
        UsernameAlreadyExists,
    )

    use_case = RegisterUserUseCase(uow)

    # Попытка создать пользователя с занятым username
    try:
        dto = RegisterUserDTO(
            username="existing_user", email="new@example.com", password="ValidPass123"
        )
        await use_case.execute(dto)
    except UsernameAlreadyExists as e:
        print(f"❌ Бизнес-ошибка: {e.message}")
        print(f"   HTTP код: {e.status_code}")

    # Попытка создать пользователя со слабым паролем
    try:
        dto = RegisterUserDTO(
            username="new_user",
            email="new2@example.com",
            password="123",  # ❌ Слишком короткий
        )
        await use_case.execute(dto)
    except InvalidPasswordFormat as e:
        print(f"❌ Валидация пароля: {e.message}")


# =====================================================
# Пример 12: Правильный поток данных (Data Flow)
# =====================================================


async def correct_data_flow_example():
    """
    Демонстрация правильного потока данных в Clean Architecture.

    HTTP Request → Controller → Use Case → Repository → Database
                                ↓
    HTTP Response ← Pydantic Schema ← Domain Entity ← Mapper ← ORM
    """

    print("=== ПРАВИЛЬНЫЙ ПОТОК ДАННЫХ ===")
    print()
    print("1. HTTP Request (RegisterRequest)")
    print("   ↓")
    print("2. API Controller преобразует в DTO (RegisterUserDTO)")
    print("   ↓")
    print("3. Use Case.execute(dto)")
    print("   ├─ Валидация через Password VO")
    print("   ├─ Создание User Entity")
    print("   ├─ Проверка бизнес-правил")
    print("   └─ Repository.create_user(user)")
    print("      ↓")
    print("4. Repository")
    print("   ├─ Mapper.to_orm(user) → UserORM")
    print("   └─ session.add(user_orm)")
    print("      ↓")
    print("5. UoW автоматически делает COMMIT")
    print("   ↓")
    print("6. Repository.get_by_id()")
    print("   ├─ SELECT * FROM users")
    print("   └─ Mapper.to_domain(user_orm) → User")
    print("      ↓")
    print("7. Controller преобразует User → RegisterResponse (Pydantic)")
    print("   ↓")
    print("8. HTTP Response (JSON)")
    print()
    print("✅ Зависимости направлены ВНУТРЬ (к Domain)")
    print("✅ Domain НЕ знает о FastAPI, SQLAlchemy, Pydantic")
    print("✅ Use Case управляет бизнес-логикой")
    print("✅ UoW управляет транзакциями")


# =====================================================
# Пример 13: Анти-паттерны (чего НЕ делать)
# =====================================================


async def anti_patterns_example():
    """
    Примеры НЕПРАВИЛЬНОГО использования (анти-паттерны).
    """

    print("=== АНТИ-ПАТТЕРНЫ (НЕ ДЕЛАТЬ ТАК!) ===")
    print()

    # ❌ НЕПРАВИЛЬНО: SQL в контроллере
    print("❌ 1. SQL в контроллере:")
    print("   @router.post('/register/')")
    print("   async def register(...):")
    print("       user = await db.execute('INSERT INTO users ...')")
    print("       ↑ Нарушение: бизнес-логика в Presentation Layer")
    print()

    # ❌ НЕПРАВИЛЬНО: ORM модели в контроллере
    print("❌ 2. Работа с ORM в контроллере:")
    print("   @router.post('/register/')")
    print("   async def register(...):")
    print("       user_orm = UserORM(username=...)")
    print("       session.add(user_orm)")
    print("       ↑ Нарушение: контроллер знает о БД")
    print()

    # ❌ НЕПРАВИЛЬНО: Domain зависит от Infrastructure
    print("❌ 3. Domain импортирует Infrastructure:")
    print("   # domain/entities/user.py")
    print("   from app.infrastructure.database.models import UserORM")
    print("   ↑ Нарушение: зависимость направлена НАРУЖУ")
    print()

    # ❌ НЕПРАВИЛЬНО: Use Case без DTO
    print("❌ 4. Use Case без DTO:")
    print("   async def execute(self, username, email, password):")
    print("       ↑ Нарушение: много параметров, нет валидации")
    print()

    # ❌ НЕПРАВИЛЬНО: Контроллер управляет транзакциями
    print("❌ 5. Контроллер делает commit:")
    print("   user = await use_case.execute(...)")
    print("   await session.commit()  # ← ПЛОХО!")
    print("   ↑ Нарушение: транзакции должен управлять UoW")
    print()

    print("✅ ПРАВИЛЬНО: Use Case + UoW + DTO + DI")


# =====================================================
# Пример 14: Сравнение старого и нового подхода
# =====================================================


async def before_after_comparison():
    """
    Сравнение архитектуры ДО и ПОСЛЕ рефакторинга.
    """

    print("=== ДО РЕФАКТОРИНГА (старый код) ===")
    print()

    print("@router.post('/register/')")
    print("async def register(request: RegisterRequest, db: Session):")
    print("    # Проверка на существование")
    print(
        "    existing = db.query(UserORM).filter_by(username=request.username).first()"
    )
    print("    if existing:")
    print("        raise HTTPException(409, 'User exists')")
    print()
    print("    # Хеширование")
    print("    hashed = bcrypt.hash(request.password)")
    print()
    print("    # Создание")
    print("    user = UserORM(username=request.username, hashed_password=hashed)")
    print("    db.add(user)")
    print("    db.commit()")
    print("    db.refresh(user)")
    print("    return user")
    print()

    print("❌ Проблемы:")
    print("   - Бизнес-логика в контроллере")
    print("   - Работа с ORM напрямую")
    print("   - Транзакции в контроллере")
    print("   - Нет валидации пароля")
    print("   - Трудно тестировать")
    print()

    print("=== ПОСЛЕ РЕФАКТОРИНГА (Clean Architecture) ===")
    print()

    print("@router.post('/register/', response_model=RegisterResponse)")
    print("async def register(")
    print("    request: RegisterRequest,")
    print("    register_use_case: GetRegisterUseCaseDep,")
    print(") -> RegisterResponse:")
    print("    dto = RegisterUserDTO(**request.model_dump())")
    print("    user = await register_use_case.execute(dto)")
    print("    return RegisterResponse.model_validate(user)")
    print()

    print("✅ Преимущества:")
    print("   - Бизнес-логика в Use Case")
    print("   - Domain Entity вместо ORM")
    print("   - UoW управляет транзакциями")
    print("   - Password VO валидирует")
    print("   - Легко тестировать (моки)")


# =====================================================
# Резюме: Правила использования Domain Layer
# =====================================================


"""
📚 ПРАВИЛА ИСПОЛЬЗОВАНИЯ DOMAIN LAYER:

1. ✅ Use Cases получают DTO, а не отдельные параметры
2. ✅ Use Cases работают через UoW, а не напрямую с репозиториями
3. ✅ Транзакциями управляет UoW (через yield в dependencies)
4. ✅ Валидация через Value Objects (Password, UserIdentity)
5. ✅ Domain Entity возвращается из Use Case
6. ✅ Mapper изолирует Domain от ORM
7. ✅ Dependency Injection через FastAPI Depends
8. ✅ Контроллер только преобразует данные (Schema ↔ Entity)

❌ НЕ ДЕЛАТЬ:
1. ❌ SQL/ORM в контроллере
2. ❌ Бизнес-логика в Presentation Layer
3. ❌ Domain импортирует Infrastructure
4. ❌ Контроллер управляет транзакциями
5. ❌ Use Case без DTO
6. ❌ Валидация в контроллере (должна быть в VO)

🎯 ЦЕЛЬ:
- Независимость Domain Layer
- Тестируемость без БД
- Переиспользование логики
- Четкое разделение ответственности
"""
