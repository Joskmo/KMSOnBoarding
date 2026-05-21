"""CRUD operations for tests."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Test


async def get(db: AsyncSession, test_id: UUID) -> Test | None:
    """Get a test by ID."""
    result = await db.execute(
        select(Test).options(selectinload(Test.questions)).where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


async def get_with_questions(db: AsyncSession, test_id: UUID) -> Test | None:
    """Get a test with its questions by ID."""
    result = await db.execute(
        select(Test).options(selectinload(Test.questions)).where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


async def get_multi(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    module_id: UUID | None = None,
    author_id: UUID | None = None,
    manager_id: UUID | None = None,
    is_active: bool | None = None,
) -> tuple[list[Test], int]:
    """Get multiple tests with optional filtering and total count."""
    query = select(Test).options(selectinload(Test.questions))
    count_query = select(func.count(Test.id))

    if module_id is not None:
        query = query.where(Test.module_id == module_id)
        count_query = count_query.where(Test.module_id == module_id)
    if author_id is not None:
        query = query.where(Test.author_id == author_id)
        count_query = count_query.where(Test.author_id == author_id)
    if manager_id is not None:
        query = query.where(Test.manager_id == manager_id)
        count_query = count_query.where(Test.manager_id == manager_id)
    if is_active is not None:
        query = query.where(Test.is_active == is_active)
        count_query = count_query.where(Test.is_active == is_active)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), count_result.scalar_one()


async def create(db: AsyncSession, *, obj_in: dict) -> Test:
    """Create a new test."""
    db_obj = Test(**obj_in)
    db.add(db_obj)
    await db.flush()
    return db_obj


async def update(db: AsyncSession, *, db_obj: Test, obj_in: dict) -> Test:
    """Update a test."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    return db_obj


async def delete(db: AsyncSession, *, db_obj: Test) -> None:
    """Delete a test."""
    await db.delete(db_obj)
