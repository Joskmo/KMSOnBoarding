"""API endpoints for tests."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import question as question_crud, test as test_crud
from app.db.models import Test
from app.db.session import get_db
from app.schemas import (
    PaginatedTests,
    QuestionCreate,
    QuestionResponse,
    TestCreate,
    TestResponse,
    TestUpdate,
)

router = APIRouter(prefix="/tests", tags=["tests"])


def _can_access_test(current_user: dict, test: Test) -> bool:
    """Check if current user can access a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return True
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


@router.post("", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    test_in: TestCreate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Test:
    """Create a new test."""
    test_data = test_in.model_dump()
    test_data["author_id"] = current_user["id"]
    test_data["manager_id"] = current_user["id"]

    test = await test_crud.create(db, obj_in=test_data)
    return await test_crud.get_with_questions(db, test.id)


@router.get("", response_model=PaginatedTests)
async def list_tests(
    module_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List tests with RBAC filtering."""
    role = current_user["role"]

    if role == "admin":
        author_id = None
        manager_id = None
        is_active = None
    elif role == "methodist":
        author_id = None if module_id is not None else current_user["id"]
        manager_id = None
        is_active = None
    else:
        # seminarist/candidate: all active tests (frontend filters by accessible modules)
        author_id = None
        manager_id = None
        is_active = True

    skip = (page - 1) * size
    tests, total = await test_crud.get_multi(
        db,
        skip=skip,
        limit=size,
        module_id=module_id,
        author_id=author_id,
        manager_id=manager_id,
        is_active=is_active,
    )

    return {
        "items": tests,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Test:
    """Get a test by ID."""
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

    return test


@router.patch("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: UUID,
    test_in: TestUpdate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Test:
    """Update test fields."""
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

    update_data = test_in.model_dump(exclude_unset=True)
    updated = await test_crud.update(db, db_obj=test, obj_in=update_data)
    return await test_crud.get_with_questions(db, updated.id)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a test."""
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

    await test_crud.delete(db, db_obj=test)


# ------------------------------------------------------------------
# Nested question endpoints under /tests/{test_id}
# ------------------------------------------------------------------


@router.post(
    "/{test_id}/questions",
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


@router.get(
    "/{test_id}/questions",
    response_model=list[QuestionResponse],
)
async def list_questions(
    test_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List questions for a test (admin and methodist only)."""
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

    return await question_crud.get_by_test(db, test_id)
