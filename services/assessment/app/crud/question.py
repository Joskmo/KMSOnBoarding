"""CRUD operations for questions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Question


async def get(db: AsyncSession, question_id: UUID) -> Question | None:
    """Get a question by ID."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    return result.scalar_one_or_none()


async def get_by_test(db: AsyncSession, test_id: UUID) -> list[Question]:
    """Get all questions for a test, ordered by order_index."""
    result = await db.execute(
        select(Question).where(Question.test_id == test_id).order_by(Question.order_index)
    )
    return list(result.scalars().all())


async def get_next_order_index(db: AsyncSession, test_id: UUID) -> int:
    """Get the next available order_index for a test."""
    result = await db.execute(
        select(Question.order_index)
        .where(Question.test_id == test_id)
        .order_by(Question.order_index.desc())
    )
    max_index = result.scalars().first()
    return (max_index + 1) if max_index is not None else 0


async def create(db: AsyncSession, *, obj_in: dict) -> Question:
    """Create a new question."""
    db_obj = Question(**obj_in)
    db.add(db_obj)
    await db.flush()
    return db_obj


async def update(db: AsyncSession, *, db_obj: Question, obj_in: dict) -> Question:
    """Update a question."""
    for field, value in obj_in.items():
        if value is not None:
            setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    return db_obj


async def delete(db: AsyncSession, *, db_obj: Question) -> None:
    """Delete a question."""
    await db.delete(db_obj)


async def reorder(db: AsyncSession, *, db_obj: Question, new_index: int) -> Question:
    """Reorder a question within its test."""
    old_index = db_obj.order_index
    test_id = db_obj.test_id

    if new_index == old_index:
        return db_obj

    questions = await get_by_test(db, test_id)
    questions.sort(key=lambda q: q.order_index)

    moved = None
    for idx, q in enumerate(questions):
        if q.id == db_obj.id:
            moved = questions.pop(idx)
            break

    if moved is None:
        raise ValueError("Question not found in test")

    if new_index < 0:
        new_index = 0
    if new_index >= len(questions):
        questions.append(moved)
    else:
        questions.insert(new_index, moved)

    from sqlalchemy import update

    # Phase 1: temporary indices
    for i, q in enumerate(questions):
        await db.execute(
            update(Question).where(Question.id == q.id).values(order_index=1_000_000 + i)
        )

    # Phase 2: final indices
    for i, q in enumerate(questions):
        final_index = new_index if q.id == db_obj.id else i
        await db.execute(
            update(Question).where(Question.id == q.id).values(order_index=final_index)
        )

    return db_obj
