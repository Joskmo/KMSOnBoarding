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
    max_index = result.scalars().first()
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

    # Fetch all lessons for the module, update order indices in Python,
    # and persist.  This avoids database-level unique constraint conflicts
    # that can occur with bulk UPDATE statements (especially on SQLite).
    lessons = await get_by_module(db, module_id)

    # Sort by current order_index to guarantee stable ordering
    lessons.sort(key=lambda lesson: lesson.order_index)

    # Find and remove the lesson being moved
    moved = None
    for idx, lesson in enumerate(lessons):
        if lesson.id == db_obj.id:
            moved = lessons.pop(idx)
            break

    if moved is None:
        raise ValueError("Lesson not found in module")

    # Insert at the new position, appending if the index is beyond the
    # current list so that arbitrary large gaps are preserved.
    if new_index < 0:
        new_index = 0
    if new_index >= len(lessons):
        lessons.append(moved)
    else:
        lessons.insert(new_index, moved)

    # Reassign order indices in two phases so that SQLite never sees an
    # intermediate duplicate on the unique (module_id, order_index) constraint.
    from sqlalchemy import update

    # Phase 1: move every lesson to a guaranteed-unique temporary index.
    for i, lesson in enumerate(lessons):
        await db.execute(
            update(Lesson).where(Lesson.id == lesson.id).values(order_index=1_000_000 + i)
        )
    await db.commit()

    # Phase 2: set the final indices.  The moved lesson keeps the requested
    # new_index; the remaining lessons receive sequential indices.
    for i, lesson in enumerate(lessons):
        final_index = new_index if lesson.id == db_obj.id else i
        await db.execute(
            update(Lesson).where(Lesson.id == lesson.id).values(order_index=final_index)
        )
    await db.commit()

    await db.refresh(db_obj)
    return db_obj
