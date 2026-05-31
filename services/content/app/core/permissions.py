"""Permission helpers for content service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import assignment as assignment_crud
from app.db.models import Module


async def can_access_module(current_user: dict, module: Module, db: AsyncSession) -> bool:
    """Check if current user can access a module."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        if str(module.author_id) == str(current_user["id"]):
            return True
        if module.status == "published":
            assigned_ids = await assignment_crud.get_modules_for_user(
                db, user_id=UUID(current_user["id"])
            )
            return module.id in assigned_ids
        return False
    if role in ("seminarist", "candidate"):
        if module.status != "published":
            return False
        assigned_ids = await assignment_crud.get_modules_for_user(
            db, user_id=UUID(current_user["id"])
        )
        return module.id in assigned_ids
    return False
