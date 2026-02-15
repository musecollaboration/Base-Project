# QWEN.md — Context for AI Assistant

## Project Overview

**User Authentication API** — production-ready REST API for user registration and authentication built with **FastAPI**, following **Clean Architecture** and **Domain-Driven Design (DDD)** principles.

### Key Characteristics

- **Type:** Python Web Application (REST API)
- **Framework:** FastAPI 0.128.x
- **Architecture:** Clean Architecture + DDD (Domain-Driven Design)
- **Database:** PostgreSQL with async SQLAlchemy + Alembic migrations
- **Authentication:** JWT tokens + Argon2 password hashing
- **Package Manager:** Poetry
- **Python Version:** 3.12+

### Core Features

- User registration and authentication (JWT + Argon2)
- Clean Architecture with clear layer separation
- Domain-Driven Design: Entities, Value Objects, Use Cases, Repositories
- Unit of Work pattern for transaction management
- Value Objects with validation (Password, Email, UserIdentity, UserSecurity)
- Dependency Injection via FastAPI
- Structured logging with correlation ID
- Docker Compose for local development

---

## Project Structure

```
UseCase/
├── app/                          # Application source code
│   ├── api/                      # 🟢 Presentation Layer (HTTP API)
│   │   ├── exception_handlers.py
│   │   └── v1/
│   │       ├── dependencies.py   # Use Cases wiring with UoW
│   │       ├── router.py
│   │       ├── routers/
│   │       │   ├── auth.py       # POST /register, /login
│   │       │   └── user.py       # GET /me, POST /update-user
│   │       └── schemas/          # Pydantic schemas (DTO for API)
│   │
│   ├── core/                     # 🔴 Core (Configuration)
│   │   ├── config.py             # Settings from .env
│   │   ├── dependencies.py       # Infrastructure-level deps (UoW, DB)
│   │   └── exceptions/           # Technical exceptions
│   │
│   ├── domain/                   # 🔵 Domain Layer (Business Logic)
│   │   ├── entities/             # Domain entities (User, VOs)
│   │   ├── exceptions/           # Domain exceptions
│   │   ├── interfaces/           # Abstract interfaces (ports)
│   │   │   ├── unit_of_work.py   # IUnitOfWork (ABC)
│   │   │   └── user_repository.py # UserRepository (ABC)
│   │   ├── value_objects/        # Value Objects with validation
│   │   │   ├── email.py
│   │   │   └── password.py       # Password VO (complexity validation)
│   │   ├── EXAMPLES.py
│   │   └── README.md
│   │
│   ├── infrastructure/           # 🟡 Infrastructure Layer
│   │   ├── database/
│   │   │   ├── base.py           # SQLAlchemy Base
│   │   │   ├── engine.py         # Engine, async_session_maker
│   │   │   ├── unit_of_work.py   # SqlAlchemyUnitOfWork
│   │   │   └── models/
│   │   │       └── user.py       # UserORM
│   │   ├── mappers/
│   │   │   └── user_mapper.py    # Domain Entity ↔ ORM
│   │   └── repositories/
│   │       └── user.py           # UserRepository implementation
│   │
│   ├── shared/                   # 🟣 Shared Utilities
│   │   ├── logging.py            # Structured logging + correlation_id
│   │   └── security.py           # JWT, Argon2 hashing
│   │
│   ├── use_cases/                # 🔵 Application Layer
│   │   ├── base.py               # BaseUseCase
│   │   ├── auth/
│   │   │   ├── authenticate.py
│   │   │   └── register.py       # RegisterUserUseCase + DTO
│   │   └── profile/
│   │       ├── access.py
│   │       ├── get.py
│   │       └── update.py
│   │
│   ├── lifespan.py               # FastAPI lifespan (startup/shutdown)
│   └── main.py                   # Application entry point
│
├── logs/                         # Application logs (daily rotation)
├── migrations/                   # Alembic migrations
│   ├── env.py
│   └── versions/
├── alembic.ini
├── docker-compose.yml            # PostgreSQL container
├── Makefile                      # Development commands
├── pyproject.toml                # Poetry configuration
├── requirements.txt              # pip dependencies
├── .env.example                  # Environment template
└── README.md                     # Full documentation (1472 lines)
```

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                    │
│              (api/v1/routers, schemas)                  │
│         HTTP requests, validation, serialization        │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
                     ↓
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                     │
│                    (use_cases/)                         │
│         Business logic orchestration, Use Cases         │
└────────────────────┬────────────────────────────────────┘
                     │ depends on
                     ↓
┌─────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                        │
│    (entities, value_objects, interfaces, exceptions)    │
│         Core: business rules and domain model           │
└────────────────────┬────────────────────────────────────┘
                     ↑ implements (via interfaces)
                     │
┌─────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                    │
│     (repositories, database, mappers, unit_of_work)     │
│        PostgreSQL, SQLAlchemy, JWT, external services   │
└─────────────────────────────────────────────────────────┘
```

### Key Principles

- ✅ **Dependencies point inward** — Domain Layer has no external dependencies
- ✅ **Dependency Inversion** — Infrastructure implements Domain interfaces
- ✅ **Single Responsibility** — Each layer has its own concerns
- ✅ **Testability** — Business logic can be tested without DB/HTTP

---

## Building and Running

### Prerequisites

- Python 3.12+
- Poetry (package manager)
- Docker (for PostgreSQL)

### Installation

```bash
# Install dependencies
poetry install

# Start PostgreSQL (Docker)
docker-compose up -d

# Copy environment file
cp .env.example .env

# Run migrations
poetry run alembic upgrade head
```

### Development Commands (Makefile)

```bash
# Run the application
make run

# Check code (no fixes)
make check

# Auto-fix and format
make fix

# Lint only
make lint

# Format only
make fmt
```

### Manual Commands

```bash
# Start development server
poetry run uvicorn app.main:app --reload

# Run linter
poetry run ruff check .

# Format code
poetry run ruff format .

# Run Alembic migration
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

### API Documentation

When running in dev mode, access:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Development Conventions

### Code Style

- **Line length:** 88 characters
- **Formatter:** Ruff (`ruff format`)
- **Linter:** Ruff with rules `E`, `F`, `I` (error, pyflakes, isort)
- **Import sorting:** Combined `as` imports, no forced single-line

Configured in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
fix = true
exclude = ["migrations", ".venv"]

[tool.ruff.lint]
select = ["E", "F", "I"]
```

### Testing Practices

- Domain layer is designed for unit testing without database
- Use Cases accept DTOs (frozen dataclasses) for easy mocking
- Infrastructure can be mocked via interfaces (IUnitOfWork, UserRepository)

### Key Patterns

#### Unit of Work Pattern

Transaction management at HTTP request level with automatic commit/rollback:

```python
# dependencies.py
async def get_uow():
    """UoW lives entire HTTP request thanks to yield."""
    uow = SqlAlchemyUnitOfWork(async_session_maker)
    async with uow:  # BEGIN transaction
        yield uow
    # AUTO commit on success, rollback on error
```

#### Value Objects

**Password VO** — validates password complexity before hashing:

```python
@dataclass(frozen=True)
class Password:
    value: str

    def __post_init__(self):
        # Min 8 chars, uppercase + lowercase + digit
        if len(self.value) < 8:
            raise InvalidPasswordFormat("Минимум 8 символов")
```

#### DTO Pattern

All Use Cases accept DTOs:

```python
@dataclass(frozen=True)
class RegisterUserDTO:
    username: str
    email: str
    password: str
```

#### Mapper Pattern

Isolation of Domain from Infrastructure:

```python
class UserMapper:
    @staticmethod
    def to_domain(orm: UserORM) -> User:
        """ORM → Domain Entity"""
    
    @staticmethod
    def to_orm(user: User) -> UserORM:
        """Domain Entity → ORM"""
```

---

## Configuration

### Environment Variables (.env)

```ini
# Environment
ENVIRONMENT=dev

# App
APP_NAME=Base APP
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://admin:admin1234@localhost:5433/db
DATABASE_ECHO=true

# JWT
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Environment Files

- `.env.example` — Template for configuration
- `.env.test` — Test environment settings
- `.env.prod` — Production environment settings

---

## Key Files Reference

| File | Description |
|------|-------------|
| `app/main.py` | Application entry point, exception handlers, middleware |
| `app/core/config.py` | Pydantic Settings loaded from `.env` |
| `app/domain/entities/user.py` | User Entity with UserIdentity + UserSecurity VOs |
| `app/domain/value_objects/password.py` | Password VO with complexity validation |
| `app/use_cases/auth/register.py` | RegisterUserUseCase with DTO |
| `app/infrastructure/database/unit_of_work.py` | SqlAlchemyUnitOfWork implementation |
| `app/infrastructure/mappers/user_mapper.py` | UserMapper (Domain ↔ ORM) |
| `app/shared/logging.py` | Structured logging with correlation ID |
| `app/shared/security.py` | JWT and Argon2 password hashing |

---

## Additional Resources

- **Full Documentation:** [README.md](README.md) (1472 lines with detailed examples)
- **Domain Layer Docs:** [app/domain/README.md](app/domain/README.md)
- **Domain Examples:** [app/domain/EXAMPLES.py](app/domain/EXAMPLES.py)
