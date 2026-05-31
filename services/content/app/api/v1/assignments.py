"""Cleanup endpoints for module assignments."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.crud import assignment as assignment_crud
from app.db.session import get_db

router = APIRouter(prefix="/module-assignments", tags=["module-assignments"])


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignments_by_user(
    user_id: UUID,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all module assignments for a user. Admin only."""
    await assignment_crud.delete_by_user(db, user_id=user_id)
