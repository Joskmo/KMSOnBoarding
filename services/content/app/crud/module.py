"""CRUD operations for modules."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Module


async def get(db: AsyncSession, module_id: UUID) -> Module | None:
    """Get a module by ID."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    return result.scalar_one_or_none()


async def get_multi(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    author_id: UUID | None = None,
    manager_id: UUID | None = None,
    module_ids: list[UUID] | None = None,
) -> tuple[list[Module], int]:
    """Get multiple modules with optional filtering and total count."""
    query = select(Module)
    count_query = select(func.count(Module.id))

    if status:
        query = query.where(Module.status == status)
        count_query = count_query.where(Module.status == status)
    if author_id:
        query = query.where(Module.author_id == author_id)
        count_query = count_query.where(Module.author_id == author_id)
    if manager_id:
        query = query.where(Module.manager_id == manager_id)
        count_query = count_query.where(Module.manager_id == manager_id)
    if module_ids is not None:
        query = query.where(Module.id.in_(module_ids))
        count_query = count_query.where(Module.id.in_(module_ids))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), count_result.scalar_one()


async def create(db: AsyncSession, *, obj_in: dict) -> Module:
    """Create a new module."""
    db_obj = Module(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update(db: AsyncSession, *, db_obj: Module, obj_in: dict) -> Module:
    """Update a module."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete(db: AsyncSession, *, db_obj: Module) -> None:
    """Delete a module."""
    await db.delete(db_obj)
    await db.commit()
