from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth import get_current_user
from app.core.enums import UserRole
from app.core.permissions import can_manage_user, can_transfer_user
from app.db.models import User
from app.db.session import get_db
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    """List users.

    Admin sees all users.
    Methodist sees only their subordinates.
    Others see only themselves.
    """
    current_role = current_user.role

    if current_role == UserRole.ADMIN:
        result = await db.execute(select(User))
    elif current_role == UserRole.METHODIST:
        result = await db.execute(select(User).where(User.manager_id == current_user.id))
    else:
        result = await db.execute(select(User).where(User.id == current_user.id))

    return list(result.scalars().all())


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not await can_manage_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access this user",
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update a user by ID.

    Supports transferring a user to another manager via manager_id.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not await can_manage_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this user",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    # Handle manager_id transfer
    if "manager_id" in update_data:
        new_manager_id = update_data["manager_id"]
        if new_manager_id and not await can_transfer_user(current_user, user, new_manager_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot transfer user to this manager",
            )

    for field, value in update_data.items():
        if field == "password" and value:
            from app.core.security import get_password_hash

            user.hashed_password = get_password_hash(value)
        else:
            setattr(user, field, value)

    await db.commit()

    result = await db.execute(select(User).where(User.id == user.id))
    return result.scalar_one()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    current_role = current_user.role
    if current_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete users",
        )

    await db.delete(user)
    await db.commit()
    return None
