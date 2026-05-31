"""Invitation management endpoints.

Provides CRUD for invitation tokens used during user registration.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.permissions import can_create_invitation, require_manager_or_admin
from app.db.models import Invitation, User
from app.db.session import get_db
from app.schemas import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
) -> Invitation:
    """Create a new invitation token for user registration."""
    creator_role = current_user.role

    if not can_create_invitation(creator_role, invitation_data.role_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя создать инвайт для этой роли",
        )

    email = invitation_data.email

    # If email is provided, check that no user with this email already exists
    if email:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Пользователь с таким email уже существует",
            )

    # If email is provided, check for an active (unused, not expired) invitation
    if email:
        result = await db.execute(
            select(Invitation).where(
                Invitation.email == email,
                Invitation.used == False,  # noqa: E712
                Invitation.expires_at > datetime.now(UTC),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Determine manager_id based on creator role and target role
    target_role = invitation_data.role_name
    manager_id = invitation_data.manager_id

    if target_role == UserRole.METHODIST:
        # Methodist is independent — no manager
        manager_id = None
    elif creator_role == UserRole.METHODIST:
        # Methodist inviting candidate/seminarist: auto-assign to self if not specified
        if manager_id is None:
            manager_id = current_user.id
        elif manager_id != current_user.id:
            # Methodist can only assign to themselves
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Методист может назначать подчиненных только себе",
            )
    elif creator_role == UserRole.ADMIN:
        if manager_id is None:
            # Admin inviting candidate/seminarist: auto-assign to self
            manager_id = current_user.id
        else:
            # Admin can assign to any admin or methodist
            result = await db.execute(select(User).where(User.id == manager_id))
            manager = result.scalar_one_or_none()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Менеджер не найден",
                )
            if manager.role not in (UserRole.ADMIN, UserRole.METHODIST):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Менеджер должен быть админом или методистом",
                )

    # Generate unique token
    token = str(uuid4())

    invitation = Invitation(
        token=token,
        email=invitation_data.email,
        role_name=invitation_data.role_name,
        manager_id=manager_id,
        created_by=current_user.id,
        used=False,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return invitation


@router.get("", response_model=list[InvitationResponse])
@router.get("/", response_model=list[InvitationResponse])
async def list_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
) -> list[Invitation]:
    """List invitations created by the current user (or all for admin)."""
    creator_role = current_user.role

    if creator_role == UserRole.ADMIN:
        result = await db.execute(select(Invitation))
    else:
        result = await db.execute(
            select(Invitation).where(Invitation.created_by == current_user.id)
        )

    return list(result.scalars().all())


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
) -> None:
    """Revoke an invitation by ID."""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Инвайт не найден",
        )

    creator_role = current_user.role
    if creator_role != UserRole.ADMIN and invitation.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя удалить этот инвайт",
        )

    await db.delete(invitation)
    await db.commit()
    return None
