"""API endpoints for lessons."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import lesson as lesson_crud, module as module_crud
from app.db.models import Lesson, Module
from app.db.session import get_db
from app.schemas import LessonReorder, LessonResponse, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["lessons"])


def _can_access_module(current_user: dict, module: Module) -> bool:
    """Check if current user can access a module."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(module.author_id) == str(current_user["id"])
    if role in ("seminarist", "candidate"):
        return module.status == "published" and str(module.manager_id) == str(
            current_user["manager_id"]
        )
    return False


def _can_modify_module(current_user: dict, module: Module) -> bool:
    """Check if current user can modify a module."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(module.author_id) == str(current_user["id"])
    return False


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Get a lesson by ID."""
    lesson = await lesson_crud.get(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    module = await module_crud.get(db, lesson.module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if not _can_access_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return lesson


@router.patch("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    lesson_in: LessonUpdate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Update lesson fields."""
    lesson = await lesson_crud.get(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    module = await module_crud.get(db, lesson.module_id)
    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    update_data = lesson_in.model_dump(exclude_unset=True)
    return await lesson_crud.update(db, db_obj=lesson, obj_in=update_data)


@router.patch("/{lesson_id}/reorder", response_model=LessonResponse)
async def reorder_lesson(
    lesson_id: UUID,
    reorder_in: LessonReorder,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Reorder a lesson within its module."""
    lesson = await lesson_crud.get(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    module = await module_crud.get(db, lesson.module_id)
    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await lesson_crud.reorder(db, db_obj=lesson, new_index=reorder_in.order_index)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a lesson."""
    lesson = await lesson_crud.get(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    module = await module_crud.get(db, lesson.module_id)
    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    await lesson_crud.delete(db, db_obj=lesson)
