---
name: fastapi
description: Use when building Python APIs with FastAPI. Covers routing, Pydantic models, dependency injection, async, and OpenAPI documentation.
---

# FastAPI Skill

## Overview
FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.8+ based on standard Python type hints. It leverages Starlette for async capabilities and Pydantic for data validation, automatically generating OpenAPI and JSON Schema documentation.

## Instructions
- Use type hints for all function parameters and return types — FastAPI uses them for validation and documentation
- Define request/response models with Pydantic v2 BaseModel for automatic validation and serialization
- Use dependency injection with `Depends()` for shared logic — authentication, database sessions, permissions
- Prefer `async` route handlers for I/O-bound operations (database queries, HTTP calls, file I/O)
- Use `BackgroundTasks` for non-blocking post-processing (email notifications, logging, webhooks)
- Organize routes with `APIRouter` prefix and tags for clean API documentation grouping
- Validate query parameters, path parameters, and request bodies using type hints and Pydantic models
- Use `HTTPException` with proper status codes for error responses; implement custom exception handlers
- Configure CORS middleware with `CORSMiddleware` for frontend integration
- Set up proper logging with Python's `logging` module or structlog for production debugging
- Use `uvicorn` with `--reload` for development and gunicorn + uvicorn workers for production

## Core Concepts

### Pydantic Models
- `BaseModel` for request/response validation
- Field types: `str`, `int`, `float`, `bool`, `datetime`, `UUID`, `EmailStr`, `HttpUrl`
- Field validation: `Field(min_length=1, max_length=100, default=...)`, `Field(ge=0, le=100)`
- Nested models for complex request bodies
- `model_validator` for cross-field validation (Pydantic v2)
- `field_validator` for individual field validation
- `ConfigDict` for model configuration (extra fields, frozen, etc.)
- `model_dump()` and `model_dump_json()` for serialization
- Response models filter out fields not defined in the model (security: never leak passwords)

### Dependency Injection
- `Depends()` for reusable components
- Dependencies can be functions, classes, or async generators
- Dependency scope is per-request by default
- Use `yield` for context managers (database sessions that need cleanup)
- `Depends()` can be nested — dependencies can depend on other dependencies
- Sub-dependencies are resolved and cached within a request
- Use `Annotated` (Python 3.9+) for cleaner dependency typing: `db: Annotated[Session, Depends(get_db)]`

### Routing
- `@app.get()`, `@app.post()`, `@app.put()`, `@app.patch()`, `@app.delete()`
- Path parameters: `{param}` — accessed as function parameter with same name
- Query parameters: function parameters not in path are auto-detected as query params
- Request body: Pydantic model parameter automatically parsed from JSON body
- Response model: `response_model` parameter on route decorator
- Status codes: `status_code` parameter or `Response(status_code=201)`
- Tags: `tags=["users"]` for grouping in OpenAPI docs
- Summary and description for enhanced documentation

### Async Support
- Async route handlers: `async def` for non-blocking processing
- Use `httpx.AsyncClient` for async HTTP calls
- Use `databases` or `SQLAlchemy async` for async database access
- `BackgroundTasks` run after the response is sent — for non-critical operations
- Sync routes work too — FastAPI runs them in a thread pool
- Use `asyncio.gather()` for concurrent async operations
- All middleware can be async; use `@app.middleware("http")` for custom middleware

### OpenAPI Documentation
- Auto-generated at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- Schema generated from Pydantic models and route parameters
- Customize with `title`, `description`, `version`, `contact`, `license` in FastAPI app constructor
- Add examples with `examples` parameter in `Field` or route parameter
- Use `responses` decorator parameter for documenting error responses
- Use `operation_id` for custom operation identifiers
- Tags with `openapi_tags` metadata for group descriptions

## Examples

### Basic API Setup
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID, uuid4

app = FastAPI(
    title="User Management API",
    version="1.0.0",
    description="API for managing users in the system",
)

# In-memory storage for example
users_db: dict[UUID, dict] = {}

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150, default=None)

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    age: Optional[int] = None
    is_active: bool = True

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    user_id = uuid4()
    user_data = user.model_dump()
    user_data["id"] = user_id
    user_data["is_active"] = True
    users_db[user_id] = user_data
    return user_data

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID):
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 10):
    return list(users_db.values())[skip:skip + limit]
```

### Dependency Injection with Database
```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import Annotated

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Type alias for cleaner annotations
DbSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(token: str = Depends(oauth2_scheme), db: DbSession) -> User:
    user = await authenticate_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/me")
async def read_current_user(current_user: CurrentUser, db: DbSession):
    return current_user
```

### Background Tasks and File Uploads
```python
from fastapi import BackgroundTasks, File, UploadFile, FastAPI
from pathlib import Path

async def send_welcome_email(email: str, user_id: str):
    await mail_service.send(
        to=email,
        subject="Welcome!",
        body=f"User {user_id} created",
    )

@app.post("/users/with-welcome")
async def create_user_with_welcome(
    user: UserCreate,
    background_tasks: BackgroundTasks,
):
    user_id = uuid4()
    users_db[user_id] = user.model_dump() | {"id": user_id}
    background_tasks.add_task(send_welcome_email, user.email, str(user_id))
    return {"id": user_id, "message": "User created"}

@app.post("/upload-avatar")
async def upload_avatar(
    user_id: UUID,
    file: UploadFile = File(...),
):
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(400, "Only JPEG/PNG allowed")
    contents = await file.read()
    path = Path(f"avatars/{user_id}{Path(file.filename).suffix}")
    path.write_bytes(contents)
    return {"filename": file.filename, "size": len(contents)}
```

### Custom Exception Handler
```python
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.code,
        content={"error": exc.message, "type": "app_error"},
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": str(exc), "type": "validation_error"},
    )

# Usage
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise AppError("Invalid item ID", 400)
    return {"item_id": item_id}
```

## Best Practices
- Use `response_model_exclude_unset` for partial updates
- Use `response_model_exclude_none` to omit null fields from responses
- Configure `openapi_url` to disable docs in production: `openapi_url=None`
- Use `servers` parameter for API versioning in OpenAPI
- Set `root_path` when running behind a reverse proxy with path prefix
- Use `Query(..., alias="page-size")` for non-Pythonic query parameter names
- Use `Path(..., ge=1)` for path parameter validation
- Use `Body(..., embed=True)` for single-field request bodies
- Use `Form()` for form data (OAuth2, file uploads)
- Use `Cookie()` and `Header()` for cookie/header parameters
- Use `status.HTTP_*` constants instead of raw integers

## Common Mistakes
- Not using async database drivers with async routes (blocks the event loop)
- Exposing internal IDs or sensitive fields in API responses
- Not setting `response_model` on routes (exposes all model fields including secrets)
- Using thread-blocking libraries in async routes (sync requests, blocking DB drivers)
- Not handling database session cleanup (connection leaks)
- Using `list` as default parameter values (shared across requests — use `None`)
- Not validating file uploads (content type, size limits)
- Forgetting to await async database operations
- Using the same model for create and response (password hash leaked in response)
- Not implementing proper error handling for all routes
- Using global variables for per-request state (race conditions)
- Not setting CORS middleware correctly for frontend requests

## Libraries
- **pydantic** — data validation (v2 is significantly faster)
- **sqlalchemy** — async ORM with PostgreSQL support
- **sqlmodel** — SQLAlchemy + Pydantic integration (simplified ORM)
- **httpx** — async HTTP client
- **alembic** — database migrations
- **fastapi-users** — authentication and user management
- **python-jose** — JWT token handling
- **passlib** — password hashing (bcrypt)
- **pytest** + **httpx** — testing with TestClient
- **ujson** — faster JSON serialization (set `json_encoder`)
- **orjson** — alternative fast JSON serialization (Python 3.9+)
- **python-multipart** — form data and file upload parsing
- **redis** — caching and session storage
- **celery** — distributed task queue for heavy background jobs
- **sentry-sdk** — error monitoring

## Design Principles
- **Type-Driven Development**: Use Python type hints as the source of truth for validation and documentation
- **Automatic Documentation**: OpenAPI and JSON Schema are generated from code, not maintained separately
- **Async-First**: All routes can be async; FastAPI handles synchronous routes in a thread pool
- **Dependency Injection**: Reusable components with automatic scoping and cleanup
- **Separation of Concerns**: Routes handle HTTP concerns, dependencies handle business logic
- **Validation at the Edge**: Input is validated as early as possible at the request boundary

## Coding Standards
- Follow PEP 8 for code style
- Use `async def` for route handlers and dependencies
- Type hints on all function signatures
- Pydantic models in `schemas/` directory
- Routes organized by feature in `routers/` directory
- API versioning: `app = APIRouter(prefix="/api/v1")`
- Use `Annotated` for dependency injection (Python 3.9+)
- Use `|` operator for optional types: `str | None` instead of `Optional[str]`
- Use `config.py` for settings with Pydantic `BaseSettings`
- Use `from __future__ import annotations` for cleaner annotations
- Organize: `routers/`, `schemas/`, `services/`, `dependencies/`, `models/`, `core/`

## Performance
- Use Pydantic v2 for 5-50x faster validation than v1
- Use `orjson` or `ujson` for faster JSON serialization
- Use `asyncpg` for async PostgreSQL with connection pooling
- Enable HTTP keep-alive for connection reuse
- Use Redis caching for expensive database queries
- Use database indexing for common query patterns
- Set reasonable DB connection pool sizes (5-20 per worker)
- Use gzip/brotli compression for large responses
- Use pagination for list endpoints (never return unbounded lists)
- Use `response_model_exclude_none` to reduce payload size
- Profile with `pyinstrument` or `cProfile` to find bottlenecks

## Testing
- Use FastAPI's `TestClient` from `httpx` for integration tests
- Override dependencies with `app.dependency_overrides`
- Use `pytest-asyncio` for async test functions
- Test validation by sending invalid data and checking 422 responses
- Mock external services with `pytest-httpx` or `respx`
- Test authentication by mocking `get_current_user` dependency
- Use `tmp_path` fixture for file upload tests
- Test error handlers by sending requests that trigger specific errors
- Parametrize tests with `@pytest.mark.parametrize` for multiple scenarios
- Use factory_boy for generating test data
- Aim for > 80% coverage; 100% for critical business logic
- Use `--cov` with pytest for coverage reports
