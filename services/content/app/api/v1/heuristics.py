"""API endpoints for heuristics."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import heuristic as heuristic_crud
from app.db.models import Heuristic, Module
from app.db.session import get_db
from app.schemas import HeuristicResponse, HeuristicUpdate

router = APIRouter(prefix="/heuristics", tags=["heuristics"])


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


@router.get("/{heuristic_id}", response_model=HeuristicResponse)
async def get_heuristic(
    heuristic_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Get a heuristic by ID."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    # Check access
    role = current_user["role"]
    if role == "admin":
        return heuristic
    if role == "methodist":
        if str(heuristic.manager_id) != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return heuristic
    if role in ("seminarist", "candidate"):
        if str(heuristic.manager_id) != str(current_user["manager_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        if not heuristic.is_approved and str(heuristic.author_id) != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return heuristic

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )


@router.patch("/{heuristic_id}", response_model=HeuristicResponse)
async def update_heuristic(
    heuristic_id: UUID,
    heuristic_in: HeuristicUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Update heuristic content."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    role = current_user["role"]
    is_author = str(heuristic.author_id) == str(current_user["id"])
    is_own_manager = str(heuristic.manager_id) == str(current_user["id"])

    if role == "admin" or (role == "methodist" and is_own_manager):
        pass
    elif is_author:
        if heuristic.is_approved:
            update_data = heuristic_in.model_dump(exclude_unset=True)
            if "content" in update_data:
                update_data["pending_content"] = update_data.pop("content")
            return await heuristic_crud.update(db, db_obj=heuristic, obj_in=update_data)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    update_data = heuristic_in.model_dump(exclude_unset=True)
    return await heuristic_crud.update(db, db_obj=heuristic, obj_in=update_data)


@router.patch("/{heuristic_id}/approve", response_model=HeuristicResponse)
async def approve_heuristic(
    heuristic_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Approve a heuristic."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    if current_user["role"] == "methodist" and str(heuristic.manager_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await heuristic_crud.approve(db, db_obj=heuristic)


@router.post("/{heuristic_id}/approve-edit", response_model=HeuristicResponse)
async def approve_heuristic_edit(
    heuristic_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Approve pending edits for a heuristic."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    if current_user["role"] == "methodist" and str(heuristic.manager_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await heuristic_crud.approve_edit(db, db_obj=heuristic)


@router.post("/{heuristic_id}/reject-edit", response_model=HeuristicResponse)
async def reject_heuristic_edit(
    heuristic_id: UUID,
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> Heuristic:
    """Reject pending edits for a heuristic."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    if current_user["role"] == "methodist" and str(heuristic.manager_id) != str(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await heuristic_crud.reject_edit(db, db_obj=heuristic)


@router.delete("/{heuristic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_heuristic(
    heuristic_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a heuristic."""
    heuristic = await heuristic_crud.get(db, heuristic_id)
    if not heuristic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heuristic not found",
        )

    role = current_user["role"]
    can_delete = False

    if role == "admin" or (
        role == "methodist" and str(heuristic.manager_id) == str(current_user["id"])
    ) or str(heuristic.author_id) == str(current_user["id"]):
        can_delete = True

    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    await heuristic_crud.delete(db, db_obj=heuristic)
