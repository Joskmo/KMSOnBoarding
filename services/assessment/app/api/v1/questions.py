"""API endpoints for questions."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.crud import question as question_crud, test as test_crud
from app.db.models import Test
from app.db.session import get_db
from app.schemas import QuestionReorder, QuestionResponse, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["questions"])


def _can_modify_test(current_user: dict, test: Test) -> bool:
    """Check if current user can modify a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(test.author_id) == str(current_user["id"])
    return False


@router.patch("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    question_in: QuestionUpdate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update question fields."""
    question = await question_crud.get(db, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    test = await test_crud.get(db, question.test_id)
    if not _can_modify_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    update_data = question_in.model_dump(exclude_unset=True)
    return await question_crud.update(db, db_obj=question, obj_in=update_data)


@router.patch("/{question_id}/reorder", response_model=QuestionResponse)
async def reorder_question(
    question_id: UUID,
    reorder_in: QuestionReorder,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reorder a question within its test."""
    question = await question_crud.get(db, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    test = await test_crud.get(db, question.test_id)
    if not _can_modify_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await question_crud.reorder(db, db_obj=question, new_index=reorder_in.order_index)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a question."""
    question = await question_crud.get(db, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    test = await test_crud.get(db, question.test_id)
    if not _can_modify_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    await question_crud.delete(db, db_obj=question)
