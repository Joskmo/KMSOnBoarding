from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers.auth import get_current_user
from app.core.enums import UserRole
from app.core.permissions import can_edit_user, can_transfer_user, can_view_user
from app.db.models import Invitation, User
from app.db.session import get_db
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    """List users.

    Admin and methodist see all users.
    Others see only themselves.
    """
    current_role = current_user.role

    if current_role in (UserRole.ADMIN, UserRole.METHODIST):
        result = await db.execute(select(User))
    else:
        result = await db.execute(select(User).where(User.id == current_user.id))

    return list(result.scalars().all())


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update current user profile."""
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "password" and value:
            from app.core.security import get_password_hash

            current_user.hashed_password = get_password_hash(value)
        else:
            setattr(current_user, field, value)

    await db.commit()

    result = await db.execute(select(User).where(User.id == current_user.id))
    return result.scalar_one()


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

    if not await can_view_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому пользователю",
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

    if not await can_edit_user(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя изменить этого пользователя",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    # Field-level restrictions for non-admins
    if current_user.role != UserRole.ADMIN:
        allowed_fields = set()
        if current_user.id == user.id:
            # Can only change own full_name
            allowed_fields.add("full_name")
        elif user.manager_id == current_user.id:
            # Can only change manager_id for subordinates
            allowed_fields.add("manager_id")

        for field in list(update_data.keys()):
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Нельзя изменить поле '{field}' для этого пользователя",
                )

    # Handle manager_id transfer
    if "manager_id" in update_data:
        new_manager_id = update_data["manager_id"]
        if new_manager_id and new_manager_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Нельзя назначить пользователя самому себе в подчинение",
            )
        if new_manager_id and not await can_transfer_user(current_user, user, new_manager_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя перевести пользователя к этому менеджеру",
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


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Reset a user's password to a random one. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ может сбрасывать пароли",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    import secrets

    new_password = secrets.token_urlsafe(12)
    from app.core.security import get_password_hash

    user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return {"new_password": new_password}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a user by ID.

    Cannot delete users with active subordinates.
    Revokes all invitations created by or assigned to the user.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только админ может удалять пользователей",
        )

    # Check for active subordinates
    subordinates_result = await db.execute(select(User).where(User.manager_id == user_id))
    if subordinates_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить пользователя с активными подчиненными. Сначала переведите их.",
        )

    # Security: delete invitations created by this user
    await db.execute(delete(Invitation).where(Invitation.created_by == user_id))

    # Delete invitations where this user is assigned as manager
    await db.execute(delete(Invitation).where(Invitation.manager_id == user_id))

    # Clear used_by references to avoid FK constraint violations
    await db.execute(update(Invitation).where(Invitation.used_by == user_id).values(used_by=None))

    # Clear invited_by references to avoid FK constraint violations
    await db.execute(update(User).where(User.invited_by == user_id).values(invited_by=None))

    await db.delete(user)
    await db.commit()

    # Cleanup module assignments in content service
    import logging
    from datetime import timedelta
    from uuid import uuid4

    import httpx

    from app.core.config import get_settings
    from app.core.security import create_access_token

    settings = get_settings()
    try:
        access_token = create_access_token(
            data={"sub": str(current_user.id), "jti": str(uuid4())},
            role=current_user.role,
            expires_delta=timedelta(minutes=5),
        )
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{settings.API_GATEWAY_URL}/api/v1/module-assignments/user/{user_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except Exception:
        logging.getLogger(__name__).warning(
            "Failed to cleanup module assignments for user %s", user_id, exc_info=True
        )

    return None
