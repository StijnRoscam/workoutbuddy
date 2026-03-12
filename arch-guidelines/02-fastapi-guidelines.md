# FastAPI Guidelines

Backend architecture, patterns, and file organization.

## App Structure

```
apps/api/
├─ app/
│  ├─ __init__.py
│  ├─ main.py              # Application entry point
│  ├─ api/
│  │  ├─ deps.py          # FastAPI dependencies
│  │  └─ routes/
│  │     ├─ __init__.py
│  │     ├─ health.py     # Health check endpoint
│  │     └─ users.py      # User endpoints
│  ├─ core/
│  │  ├─ config.py        # Settings and configuration
│  │  ├─ security.py      # Auth, JWT, password hashing
│  │  ├─ logging.py       # Structured logging setup
│  │  └─ db.py            # Database connection and session
│  ├─ models/             # SQLAlchemy models
│  │  ├─ __init__.py
│  │  └─ user.py
│  ├─ schemas/            # Pydantic schemas
│  │  ├─ __init__.py
│  │  └─ user.py
│  ├─ services/           # Business logic
│  │  ├─ __init__.py
│  │  └─ user_service.py
│  ├─ repositories/       # Database access layer
│  │  ├─ __init__.py
│  │  └─ user_repository.py
│  └─ tests/
│     ├─ unit/
│     ├─ integration/
│     └─ conftest.py
├─ alembic/               # Database migrations
├─ pyproject.toml
├─ alembic.ini
└─ Dockerfile
```

## Layer Responsibilities

### API Layer (`app/api/`)

**Routes** (`routes/`): HTTP endpoints, request/response handling
- Validate input using Pydantic schemas
- Call services for business logic
- Handle HTTP-specific concerns (status codes, headers)
- Keep thin - no business logic here

**Dependencies** (`deps.py`): FastAPI dependencies
- Database session injection
- Current user extraction from JWT
- Permission checks

```python
# app/api/routes/users.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user."""
    user_service = UserService(db)
    return user_service.create(user_in)
```

### Service Layer (`app/services/`)

**Services**: Business logic, domain operations
- Orchestrate use cases
- Coordinate between repositories
- Handle transactions
- Contain business rules and validations

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create(self, user_in: UserCreate) -> User:
        # Business logic: check if email exists
        if self.repo.get_by_email(user_in.email):
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = hash_password(user_in.password)

        # Create user
        return self.repo.create(email=user_in.email, password=hashed_password)
```

### Repository Layer (`app/repositories/`)

**Repositories**: Database access abstraction
- CRUD operations
- Query building
- No business logic
- Return models, not schemas

```python
# app/repositories/user_repository.py
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password: str) -> User:
        user = User(email=email, hashed_password=password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

### Schema Layer (`app/schemas/`)

**Pydantic Schemas**: Data validation and serialization
- Request/response models
- Validation rules
- Clear separation between internal models and API contracts

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
```

### Model Layer (`app/models/`)

**SQLAlchemy Models**: Database table definitions
- Table structure
- Relationships
- Column definitions
- No business logic

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
```

## Configuration Management

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Acme API"
    environment: str = "dev"
    debug: bool = False

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
```

## Main Application

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.db import engine
from app.api.routes import health, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_db()
    yield
    # Shutdown
    await shutdown_db()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(users.router, prefix="/users", tags=["users"])
```

## Database Migrations

Use Alembic for schema migrations:

```bash
# Create migration
alembic revision --autogenerate -m "add users table"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Key Patterns

1. **Dependency Injection**: Use FastAPI's `Depends()` for database sessions and auth
2. **Request/Response Models**: Always use Pydantic schemas for API boundaries
3. **Thin Routes**: Routes handle HTTP concerns, delegate to services
4. **Service Layer**: Contains all business logic
5. **Repository Pattern**: Abstract database access
6. **Async Support**: Use `async/await` for I/O operations
7. **Type Hints**: Full type annotations everywhere
8. **OpenAPI**: Let FastAPI auto-generate from code

## OpenAPI Contract

FastAPI automatically generates OpenAPI at `/openapi.json`. This is the source of truth for the API contract.

Generate TypeScript client:
```bash
pnpm generate:client
```

This creates typed client in `packages/client-sdk/` for frontend consumption.

## Error Handling

Use custom exception handlers:

```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## Related Documents

- [Monorepo Structure](./01-monorepo-structure.md) - Repository organization
- [Next.js Guidelines](./03-nextjs-guidelines.md) - Frontend integration
- [Testing](./06-testing.md) - Testing patterns
- [Security](./07-security.md) - Authentication and authorization
