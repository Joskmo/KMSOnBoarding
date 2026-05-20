"""CRUD operations for lessons."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson


async def get(db: AsyncSession, lesson_id: UUID) -> Lesson | None:
    """Get a lesson by ID."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()


async def get_by_module(db: AsyncSession, module_id: UUID) -> list[Lesson]:
    """Get all lessons for a module, ordered by order_index."""
    result = await db.execute(
        select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.order_index)
    )
    return list(result.scalars().all())


async def get_next_order_index(db: AsyncSession, module_id: UUID) -> int:
    """Get the next available order_index for a module."""
    result = await db.execute(
        select(Lesson.order_index)
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.order_index.desc())
    )
    max_index = result.scalar_one_or_none()
    return (max_index + 1) if max_index is not None else 0


async def create(db: AsyncSession, *, obj_in: dict) -> Lesson:
    """Create a new lesson."""
    db_obj = Lesson(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update(db: AsyncSession, *, db_obj: Lesson, obj_in: dict) -> Lesson:
    """Update a lesson."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete(db: AsyncSession, *, db_obj: Lesson) -> None:
    """Delete a lesson."""
    await db.delete(db_obj)
    await db.commit()


async def reorder(db: AsyncSession, *, db_obj: Lesson, new_index: int) -> Lesson:
    """Reorder a lesson within its module."""
    old_index = db_obj.order_index
    module_id = db_obj.module_id

    if new_index == old_index:
        return db_obj

    if new_index > old_index:
        # Moving down: shift items between old+1 and new up by 1
        await db.execute(
            select(Lesson).where(
                Lesson.module_id == module_id,
                Lesson.order_index > old_index,
                Lesson.order_index <= new_index,
            )
        )
        # Update via direct SQL for efficiency
        from sqlalchemy import update

        await db.execute(
            update(Lesson)
            .where(
                Lesson.module_id == module_id,
                Lesson.order_index > old_index,
                Lesson.order_index <= new_index,
            )
            .values(order_index=Lesson.order_index - 1)
        )
    else:
        # Moving up: shift items between new and old-1 down by 1
        from sqlalchemy import update

        await db.execute(
            update(Lesson)
            .where(
                Lesson.module_id == module_id,
                Lesson.order_index >= new_index,
                Lesson.order_index < old_index,
            )
            .values(order_index=Lesson.order_index + 1)
        )

    db_obj.order_index = new_index
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
