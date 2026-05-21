"""API endpoints for questions."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import question as question_crud, test as test_crud
from app.db.models import Test
from app.db.session import get_db
from app.schemas import QuestionCreate, QuestionReorder, QuestionResponse, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["questions"])


def _can_access_test(current_user: dict, test: Test) -> bool:
    """Check if current user can access a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(test.author_id) == str(current_user["id"])
    if role in ("seminarist", "candidate"):
        return test.is_active and str(test.manager_id) == str(current_user["manager_id"])
    return False


def _can_modify_test(current_user: dict, test: Test) -> bool:
    """Check if current user can modify a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(test.author_id) == str(current_user["id"])
    return False


@router.post(
    "/tests/{test_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    test_id: UUID,
    question_in: QuestionCreate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new question in a test."""
    test = await test_crud.get(db, test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found",
        )

    if not _can_modify_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    question_data = question_in.model_dump()
    question_data["test_id"] = test_id
    if question_data.get("order_index") is None:
        question_data["order_index"] = await question_crud.get_next_order_index(db, test_id)

    return await question_crud.create(db, obj_in=question_data)


@router.get("/tests/{test_id}/questions")
async def list_questions(
    test_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List questions for a test."""
    test = await test_crud.get(db, test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found",
        )

    if not _can_access_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    questions = await question_crud.get_by_test(db, test_id)

    if current_user["role"] in ("seminarist", "candidate"):
        # Strip is_correct from options
        result = []
        for q in questions:
            q_dict = {
                "id": q.id,
                "test_id": q.test_id,
                "order_index": q.order_index,
                "text": q.text,
                "qtype": q.qtype,
                "options": [{"id": opt["id"], "text": opt["text"]} for opt in q.options],
                "created_at": q.created_at,
                "updated_at": q.updated_at,
            }
            result.append(q_dict)
        return result

    return [
        {
            "id": q.id,
            "test_id": q.test_id,
            "order_index": q.order_index,
            "text": q.text,
            "qtype": q.qtype,
            "options": q.options,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
        }
        for q in questions
    ]


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
