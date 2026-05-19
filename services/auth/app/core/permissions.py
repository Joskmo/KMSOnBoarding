"""Permission utilities for role-based access control.

Provides FastAPI dependencies to enforce role-based access control
and user hierarchy constraints.
"""

from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth import get_current_user
from app.db.models import User

ROLE_HIERARCHY = {
    "admin": 3,
    "methodist": 2,
    "seminarist": 1,
    "candidate": 0,
}


def _get_primary_role(user: User) -> str | None:
    """Return the first role name for a user, or None."""
    if not user.roles:
        return None
    return user.roles[0].name


def require_role(allowed_roles: Sequence[str]):
    """FastAPI dependency factory that allows only specified roles."""

    async def checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        primary = _get_primary_role(current_user)
        if primary not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require admin role."""
    primary = _get_primary_role(current_user)
    if primary != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_manager_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require methodist or admin role."""
    primary = _get_primary_role(current_user)
    if primary not in ("admin", "methodist"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return current_user


def can_create_invitation(creator_role: str, target_role: str) -> bool:
    """Check if a creator can invite someone with target_role."""
    if creator_role == "admin":
        return True
    if creator_role == "methodist":
        return target_role in ("methodist", "seminarist", "candidate")
    return False


async def can_transfer_user(
    current_user: User,
    target_user: User,
    new_manager_id: UUID,
    db: AsyncSession,
) -> bool:
    """Check if current_user can transfer target_user to new_manager_id."""
    current_role = _get_primary_role(current_user)
    if current_role == "admin":
        return True
    if current_role == "methodist":
        # Can only transfer own subordinates
        if target_user.manager_id != current_user.id:
            return False
        # Can only transfer to another methodist
        result = await db.execute(select(User).where(User.id == new_manager_id))
        new_manager = result.scalar_one_or_none()
        if not new_manager:
            return False
        manager_role = _get_primary_role(new_manager)
        return manager_role == "methodist"
    return False


async def can_manage_user(
    current_user: User,
    target_user: User,
) -> bool:
    """Check if current_user can view/manage target_user."""
    current_role = _get_primary_role(current_user)
    if current_role == "admin":
        return True
    if current_role == "methodist":
        return target_user.manager_id == current_user.id
    return current_user.id == target_user.id
