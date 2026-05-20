"""CRUD operations for heuristics."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Heuristic


async def get(db: AsyncSession, heuristic_id: UUID) -> Heuristic | None:
    """Get a heuristic by ID."""
    result = await db.execute(select(Heuristic).where(Heuristic.id == heuristic_id))
    return result.scalar_one_or_none()


async def get_by_module(
    db: AsyncSession,
    module_id: UUID,
    *,
    approved_only: bool = False,
    manager_id: UUID | None = None,
) -> list[Heuristic]:
    """Get heuristics for a module with optional filtering."""
    query = select(Heuristic).where(Heuristic.module_id == module_id)

    if approved_only:
        query = query.where(Heuristic.is_approved.is_(True))
    if manager_id:
        query = query.where(Heuristic.manager_id == manager_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def create(db: AsyncSession, *, obj_in: dict) -> Heuristic:
    """Create a new heuristic."""
    db_obj = Heuristic(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update(db: AsyncSession, *, db_obj: Heuristic, obj_in: dict) -> Heuristic:
    """Update a heuristic."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def approve(db: AsyncSession, *, db_obj: Heuristic) -> Heuristic:
    """Approve a heuristic."""
    db_obj.is_approved = True
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete(db: AsyncSession, *, db_obj: Heuristic) -> None:
    """Delete a heuristic."""
    await db.delete(db_obj)
    await db.commit()
