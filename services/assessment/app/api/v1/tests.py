"""API endpoints for tests."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import test as test_crud
from app.db.models import Test
from app.db.session import get_db
from app.schemas import PaginatedTests, TestCreate, TestResponse, TestUpdate

router = APIRouter(prefix="/tests", tags=["tests"])


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

    return await test_crud.create(db, obj_in=test_data)


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
        author_id = current_user["id"]
        manager_id = None
        is_active = None
    else:
        # seminarist/candidate: only active tests of their manager
        author_id = None
        manager_id = current_user["manager_id"]
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
    return await test_crud.update(db, db_obj=test, obj_in=update_data)


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
