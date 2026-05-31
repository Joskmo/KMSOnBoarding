"""CRUD operations for attempts."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Attempt


async def get(db: AsyncSession, attempt_id: UUID) -> Attempt | None:
    """Get an attempt by ID."""
    result = await db.execute(
        select(Attempt).options(selectinload(Attempt.test)).where(Attempt.id == attempt_id)
    )
    return result.scalar_one_or_none()


async def get_multi(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    test_id: UUID | None = None,
    user_id: UUID | None = None,
    manager_id: UUID | None = None,
) -> tuple[list[Attempt], int]:
    """Get multiple attempts with optional filtering and total count."""
    query = select(Attempt).options(selectinload(Attempt.test))
    count_query = select(func.count(Attempt.id))

    if test_id is not None:
        query = query.where(Attempt.test_id == test_id)
        count_query = count_query.where(Attempt.test_id == test_id)
    if user_id is not None:
        query = query.where(Attempt.user_id == user_id)
        count_query = count_query.where(Attempt.user_id == user_id)
    if manager_id is not None:
        query = query.where(Attempt.manager_id == manager_id)
        count_query = count_query.where(Attempt.manager_id == manager_id)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), count_result.scalar_one()


async def create(db: AsyncSession, *, obj_in: dict) -> Attempt:
    """Create a new attempt."""
    db_obj = Attempt(**obj_in)
    db.add(db_obj)
    await db.flush()
    return db_obj


async def get_active_by_user_and_test(
    db: AsyncSession, user_id: UUID, test_id: UUID
) -> Attempt | None:
    """Get the most recent active (unfinished) attempt by user and test."""
    result = await db.execute(
        select(Attempt)
        .where(Attempt.user_id == user_id)
        .where(Attempt.test_id == test_id)
        .where(Attempt.started_at == Attempt.finished_at)
        .order_by(Attempt.started_at.desc())
    )
    return result.scalars().first()


async def delete_by_test_id(db: AsyncSession, *, test_id: UUID) -> int:
    """Delete all attempts for a given test. Returns deleted count."""
    result = await db.execute(select(Attempt).where(Attempt.test_id == test_id))
    attempts = result.scalars().all()
    for attempt in attempts:
        await db.delete(attempt)
    return len(attempts)


async def update(db: AsyncSession, *, db_obj: Attempt, obj_in: dict) -> Attempt:
    """Update an attempt."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    return db_obj
