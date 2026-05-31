"""CRUD operations for module assignments."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ModuleAssignment


async def create_assignments(
    db: AsyncSession,
    *,
    module_id: UUID,
    user_ids: list[UUID],
    assigned_by: UUID,
) -> list[ModuleAssignment]:
    """Create assignments for users, skipping duplicates."""
    for uid in user_ids:
        existing = await db.execute(
            select(ModuleAssignment).where(
                ModuleAssignment.module_id == module_id,
                ModuleAssignment.user_id == uid,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(ModuleAssignment(module_id=module_id, user_id=uid, assigned_by=assigned_by))
    await db.commit()

    result = await db.execute(
        select(ModuleAssignment).where(
            ModuleAssignment.module_id == module_id,
            ModuleAssignment.user_id.in_(user_ids),
        )
    )
    return list(result.scalars().all())


async def delete_assignment(db: AsyncSession, *, module_id: UUID, user_id: UUID) -> None:
    """Delete a single module assignment."""
    await db.execute(
        delete(ModuleAssignment).where(
            ModuleAssignment.module_id == module_id,
            ModuleAssignment.user_id == user_id,
        )
    )
    await db.commit()


async def get_by_module(db: AsyncSession, *, module_id: UUID) -> list[ModuleAssignment]:
    """Get all assignments for a module."""
    result = await db.execute(
        select(ModuleAssignment).where(ModuleAssignment.module_id == module_id)
    )
    return list(result.scalars().all())


async def get_modules_for_user(db: AsyncSession, *, user_id: UUID) -> list[UUID]:
    """Return module IDs assigned to a user."""
    result = await db.execute(
        select(ModuleAssignment.module_id).where(ModuleAssignment.user_id == user_id)
    )
    return list(result.scalars().all())


async def delete_by_user(db: AsyncSession, *, user_id: UUID) -> None:
    """Delete all assignments for a user (cleanup hook)."""
    await db.execute(delete(ModuleAssignment).where(ModuleAssignment.user_id == user_id))
    await db.commit()
