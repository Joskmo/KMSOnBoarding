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
from app.core.enums import UserRole
from app.db.models import User

ROLE_HIERARCHY = {
    UserRole.ADMIN: 3,
    UserRole.METHODIST: 2,
    UserRole.SEMINARIST: 1,
    UserRole.CANDIDATE: 0,
}


def require_role(allowed_roles: Sequence[str]):
    """FastAPI dependency factory that allows only specified roles."""

    async def checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_manager_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require methodist or admin role."""
    if current_user.role not in (UserRole.ADMIN, UserRole.METHODIST):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return current_user


def can_create_invitation(creator_role: str, target_role: str) -> bool:
    """Check if a creator can invite someone with target_role."""
    if creator_role == UserRole.ADMIN:
        return True
    if creator_role == UserRole.METHODIST:
        return target_role in (
            UserRole.METHODIST,
            UserRole.SEMINARIST,
            UserRole.CANDIDATE,
        )
    return False


async def can_transfer_user(
    current_user: User,
    target_user: User,
    new_manager_id: UUID,
    db: AsyncSession,
) -> bool:
    """Check if current_user can transfer target_user to new_manager_id."""
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.role == UserRole.METHODIST:
        # Can only transfer own subordinates
        if target_user.manager_id != current_user.id:
            return False
        # Can only transfer to another methodist
        result = await db.execute(select(User).where(User.id == new_manager_id))
        new_manager = result.scalar_one_or_none()
        if not new_manager:
            return False
        return new_manager.role == UserRole.METHODIST
    return False


async def can_manage_user(
    current_user: User,
    target_user: User,
) -> bool:
    """Check if current_user can view/manage target_user."""
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.role == UserRole.METHODIST:
        return (
            target_user.manager_id == current_user.id
            or current_user.id == target_user.id
        )
    return current_user.id == target_user.id
