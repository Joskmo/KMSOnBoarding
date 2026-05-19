"""Invitation management endpoints.

Provides CRUD for invitation tokens used during user registration.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import can_create_invitation, require_manager_or_admin
from app.db.models import Invitation, Role, User
from app.db.session import get_db
from app.schemas import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
) -> Invitation:
    """Create a new invitation token for user registration."""
    creator_role = current_user.roles[0].name if current_user.roles else ""

    # Validate role exists
    result = await db.execute(select(Role).where(Role.id == invitation_data.role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if not can_create_invitation(creator_role, role.name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create invitation for this role",
        )

    # Generate unique token
    token = str(uuid4())

    invitation = Invitation(
        token=token,
        email=invitation_data.email,
        role_id=invitation_data.role_id,
        manager_id=invitation_data.manager_id,
        created_by=current_user.id,
        used=False,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return invitation


@router.get("/", response_model=list[InvitationResponse])
async def list_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_or_admin),
) -> list[Invitation]:
    """List invitations created by the current user (or all for admin)."""
    creator_role = current_user.roles[0].name if current_user.roles else ""

    if creator_role == "admin":
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
            detail="Invitation not found",
        )

    creator_role = current_user.roles[0].name if current_user.roles else ""
    if creator_role != "admin" and invitation.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete this invitation",
        )

    await db.delete(invitation)
    await db.commit()
    return None
