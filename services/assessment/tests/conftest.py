"""Pytest fixtures and helpers for assessment service tests."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

# Monkeypatch SQLite UUID rendering to CHAR(32) to avoid numeric affinity issues
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

_original_visit_UUID = SQLiteTypeCompiler.visit_UUID


def _visit_UUID_fixed(self, type_, **kw):
    """Render UUID as CHAR(32) for SQLite to prevent numeric conversion."""
    return self._render_string_type("CHAR", length=32, collation=None)


SQLiteTypeCompiler.visit_UUID = _visit_UUID_fixed

# Monkeypatch Uuid bind_processor to accept string UUIDs
from sqlalchemy.sql.sqltypes import Uuid

_original_uuid_bind_processor = Uuid.bind_processor


def _fixed_bind_processor(self, dialect):
    original = _original_uuid_bind_processor(self, dialect)
    if original is None:
        return None

    def process(value):
        if value is not None and isinstance(value, str):
            return value.replace("-", "")
        return original(value)

    return process


Uuid.bind_processor = _fixed_bind_processor

from app.core.config import get_settings
from app.core.deps import get_redis_pool
from app.core.redis import close_redis_pool
from app.db.models import Base
from app.db.session import get_db
from app.main import app

settings = get_settings()
settings.SECRET_KEY = "test-secret"
settings.ALGORITHM = "HS256"

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    future=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Fixed UUIDs for testing
ADMIN_ID = UUID("11111111-1111-1111-1111-111111111111")
METHODIST_1_ID = UUID("22222222-2222-2222-2222-222222222222")
METHODIST_2_ID = UUID("33333333-3333-3333-3333-333333333333")
SEMINARIST_ID = UUID("44444444-4444-4444-4444-444444444444")
CANDIDATE_ID = UUID("55555555-5555-5555-5555-555555555555")


class FakeRedis:
    """Fake Redis client that always returns None for blacklist checks."""

    async def get(self, key: str) -> None:
        return None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        pass

    async def aclose(self) -> None:
        pass


async def override_get_db() -> AsyncGenerator[AsyncSession]:
    """Override get_db dependency with a test database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def override_get_redis_pool() -> FakeRedis:
    """Override Redis with a fake client."""
    return FakeRedis()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis_pool] = override_get_redis_pool


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None]:
    """Create and drop database tables for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_redis_pool()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Provide a direct database session for test helpers."""
    async with async_session() as session:
        yield session
        await session.close()


def create_token(
    user_id: UUID,
    role: str,
    manager_id: UUID | None = None,
) -> str:
    """Generate a JWT access token for testing."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "role": role,
        "manager_id": str(manager_id) if manager_id else None,
        "jti": str(uuid4()),
        "exp": now + timedelta(hours=1),
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture
def admin_token() -> str:
    return create_token(ADMIN_ID, "admin")


@pytest.fixture
def methodist1_token() -> str:
    return create_token(METHODIST_1_ID, "methodist")


@pytest.fixture
def methodist2_token() -> str:
    return create_token(METHODIST_2_ID, "methodist")


@pytest.fixture
def seminarist_token() -> str:
    return create_token(SEMINARIST_ID, "seminarist", manager_id=METHODIST_1_ID)


@pytest.fixture
def candidate_token() -> str:
    return create_token(CANDIDATE_ID, "candidate", manager_id=METHODIST_1_ID)


# ------------------------------------------------------------------
# DB helper functions
# ------------------------------------------------------------------

from app.crud import attempt as attempt_crud, question as question_crud, test as test_crud


async def create_test(
    db: AsyncSession,
    module_id: UUID | None = None,
    title: str = "Test Module",
    description: str | None = None,
    pass_score: int = 70,
    author_id: UUID | None = None,
    manager_id: UUID | None = None,
    is_active: bool = True,
) -> UUID:
    """Create a test directly in the database."""
    test = await test_crud.create(
        db,
        obj_in={
            "module_id": str(module_id or uuid4()),
            "title": title,
            "description": description,
            "pass_score": pass_score,
            "author_id": author_id or METHODIST_1_ID,
            "manager_id": manager_id or METHODIST_1_ID,
            "is_active": is_active,
        },
    )
    return test.id


async def create_question(
    db: AsyncSession,
    test_id: UUID,
    text: str = "Sample question?",
    qtype: str = "single",
    order_index: int | None = None,
    options: list[dict] | None = None,
) -> UUID:
    """Create a question directly in the database."""
    if options is None:
        options = [
            {"id": "a", "text": "Option A", "is_correct": True},
            {"id": "b", "text": "Option B", "is_correct": False},
        ]
    if order_index is None:
        order_index = await question_crud.get_next_order_index(db, test_id)
    question = await question_crud.create(
        db,
        obj_in={
            "test_id": test_id,
            "text": text,
            "qtype": qtype,
            "order_index": order_index,
            "options": options,
        },
    )
    return question.id


async def create_attempt(
    db: AsyncSession,
    test_id: UUID,
    user_id: UUID,
    manager_id: UUID | None = None,
    answers: dict | None = None,
    score: int = 0,
    is_passed: bool = False,
) -> UUID:
    """Create an attempt directly in the database."""
    attempt = await attempt_crud.create(
        db,
        obj_in={
            "test_id": test_id,
            "user_id": user_id,
            "manager_id": manager_id or METHODIST_1_ID,
            "answers": answers or {},
            "score": score,
            "is_passed": is_passed,
        },
    )
    return attempt.id
