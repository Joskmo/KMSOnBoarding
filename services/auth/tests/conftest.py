import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.models import Base, Role
from app.db.session import get_db
from app.main import app

settings = get_settings()
TEST_DATABASE_URL = "postgresql+asyncpg://kms:kms@localhost:5433/kms_auth_test"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
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


app.dependency_overrides[get_db] = override_get_db


ROLES = [
    {"name": "admin", "description": "Administrator with full access"},
    {"name": "methodist", "description": "Content creator and manager"},
    {"name": "seminarist", "description": "Seminar conductor"},
    {"name": "candidate", "description": "Learner and test taker"},
]


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and drop database tables for each test, seed roles."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        for role_data in ROLES:
            session.add(Role(**role_data))
        await session.commit()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Provide an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db():
    """Provide a direct database session for test helpers."""
    async with async_session() as session:
        yield session
        await session.close()
