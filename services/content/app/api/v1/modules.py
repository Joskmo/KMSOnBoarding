"""API endpoints for modules."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import heuristic as heuristic_crud, lesson as lesson_crud, module as module_crud
from app.db.models import Heuristic, Lesson, Module
from app.db.session import get_db
from app.schemas import (
    HeuristicCreate,
    HeuristicResponse,
    LessonCreate,
    LessonResponse,
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
    PaginatedModules,
)

router = APIRouter(prefix="/modules", tags=["modules"])


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


@router.post(
    "",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    module_in: ModuleCreate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Module:
    """Create a new module."""
    module_data = module_in.model_dump()
    module_data["author_id"] = current_user["id"]
    module_data["manager_id"] = current_user["id"]

    return await module_crud.create(db, obj_in=module_data)


@router.get("", response_model=PaginatedModules)
async def list_modules(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List modules with RBAC filtering."""
    role = current_user["role"]

    if role == "admin":
        author_id = None
        manager_id = None
    elif role == "methodist":
        author_id = current_user["id"]
        manager_id = None
    else:
        # seminarist/candidate: only published modules of their manager
        author_id = None
        manager_id = current_user["manager_id"]
        if not status_filter:
            status_filter = "published"

    skip = (page - 1) * size
    modules, total = await module_crud.get_multi(
        db,
        skip=skip,
        limit=size,
        status=status_filter,
        author_id=author_id,
        manager_id=manager_id,
    )

    return {
        "items": modules,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Module:
    """Get a module by ID."""
    module = await module_crud.get(db, module_id)
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

    return module


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: UUID,
    module_in: ModuleUpdate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Module:
    """Update module fields."""
    module = await module_crud.get(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    update_data = module_in.model_dump(exclude_unset=True)
    return await module_crud.update(db, db_obj=module, obj_in=update_data)


@router.patch("/{module_id}/status", response_model=ModuleResponse)
async def update_module_status(
    module_id: UUID,
    status_update: dict,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Module:
    """Update module status."""
    module = await module_crud.get(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status is required",
        )

    # Business rule: published -> draft is forbidden
    if module.status == "published" and new_status == "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot revert published module to draft",
        )

    return await module_crud.update(db, db_obj=module, obj_in={"status": new_status})


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a module."""
    module = await module_crud.get(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    if current_user["role"] == "methodist" and module.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft modules can be deleted",
        )

    await module_crud.delete(db, db_obj=module)


# ------------------------------------------------------------------
# Nested lesson endpoints under /modules/{module_id}
# ------------------------------------------------------------------


@router.post(
    "/{module_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    module_id: UUID,
    lesson_in: LessonCreate,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Create a new lesson in a module."""
    module = await module_crud.get(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if not _can_modify_module(current_user, module):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    lesson_data = lesson_in.model_dump()
    lesson_data["module_id"] = module_id
    lesson_data["author_id"] = current_user["id"]

    if lesson_data.get("order_index") is None:
        lesson_data["order_index"] = await lesson_crud.get_next_order_index(db, module_id)

    return await lesson_crud.create(db, obj_in=lesson_data)


@router.get("/{module_id}/lessons", response_model=list[LessonResponse])
async def list_lessons(
    module_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Lesson]:
    """List lessons for a module."""
    module = await module_crud.get(db, module_id)
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

    return await lesson_crud.get_by_module(db, module_id)


# ------------------------------------------------------------------
# Nested heuristic endpoints under /modules/{module_id}
# ------------------------------------------------------------------


@router.post(
    "/{module_id}/heuristics",
    response_model=HeuristicResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_heuristic(
    module_id: UUID,
    heuristic_in: HeuristicCreate,
    current_user: dict = Depends(require_role(["admin", "seminarist", "candidate"])),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Create a new heuristic for a published module."""
    module = await module_crud.get(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )

    if current_user["role"] in ("seminarist", "candidate"):
        if module.status != "published":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only add heuristics to published modules",
            )
        if str(module.manager_id) != str(current_user["manager_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Module does not belong to your manager",
            )

    heuristic_data = heuristic_in.model_dump()
    heuristic_data["module_id"] = module_id
    heuristic_data["author_id"] = current_user["id"]
    heuristic_data["manager_id"] = current_user["manager_id"] or current_user["id"]

    return await heuristic_crud.create(db, obj_in=heuristic_data)


@router.get("/{module_id}/heuristics", response_model=list[HeuristicResponse])
async def list_heuristics(
    module_id: UUID,
    approved_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Heuristic]:
    """List heuristics for a module."""
    module = await module_crud.get(db, module_id)
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

    role = current_user["role"]
    manager_id = None
    if role in ("seminarist", "candidate"):
        manager_id = current_user["manager_id"]

    heuristics = await heuristic_crud.get_by_module(
        db, module_id, approved_only=approved_only, manager_id=manager_id
    )

    # Additional filtering for seminarist/candidate: only show their own unapproved
    if role in ("seminarist", "candidate"):
        filtered = []
        for h in heuristics:
            if h.is_approved or str(h.author_id) == str(current_user["id"]):
                filtered.append(h)
        heuristics = filtered

    return heuristics
