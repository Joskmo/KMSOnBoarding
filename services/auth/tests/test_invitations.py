from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.enums import UserRole
from app.db.models import Invitation, Role


async def create_user(client, email, password, full_name, invitation_token=None):
    """Helper to create a user via registration endpoint."""
    payload = {"email": email, "password": password, "full_name": full_name}
    if invitation_token:
        payload["invitation_token"] = invitation_token
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


async def login_user(client, email, password):
    """Helper to login and return access token."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_can_create_invitation_for_any_role(client, db):
    """Admin can create invitation for methodist role."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.METHODIST))
    methodist_role = role_result.fetchone()
    role_id = str(methodist_role.id)

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "new@example.com",
            "role_id": role_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["used"] is False
    assert "token" in data


@pytest.mark.asyncio
async def test_methodist_can_create_invitation_for_candidate(client, db):
    """Methodist can create invitation for candidate."""
    # Create admin first to invite methodist
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.METHODIST))
    methodist_role = role_result.fetchone()

    # Admin invites methodist
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "methodist@example.com",
            "role_id": str(methodist_role.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    # Methodist registers
    _ = await create_user(
        client, "methodist@example.com", "password123", "Methodist", invitation_token=invite_token
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    # Methodist invites candidate
    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_id": str(candidate_role.id),
        },
        headers={"Authorization": f"Bearer {methodist_token}"},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_methodist_cannot_create_invitation_for_admin(client, db):
    """Methodist cannot create invitation for admin role."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.METHODIST))
    methodist_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "methodist@example.com",
            "role_id": str(methodist_role.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    await create_user(
        client, "methodist@example.com", "password123", "Methodist", invitation_token=invite_token
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.ADMIN))
    admin_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "new_admin@example.com",
            "role_id": str(admin_role.id),
        },
        headers={"Authorization": f"Bearer {methodist_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_with_valid_invitation(client, db):
    """User can register with a valid invitation token."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_id": str(candidate_role.id),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    invite_token = response.json()["token"]

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate User",
            "invitation_token": invite_token,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "candidate@example.com"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["name"] == UserRole.CANDIDATE


@pytest.mark.asyncio
async def test_register_with_used_invitation(client, db):
    """Registration with used invitation token fails."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_id": str(candidate_role.id),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    invite_token = response.json()["token"]

    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate User",
            "invitation_token": invite_token,
        },
    )

    # Second registration with same token
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate2@example.com",
            "password": "password123",
            "full_name": "Candidate 2",
            "invitation_token": invite_token,
        },
    )
    assert response.status_code == 400
    assert "already used" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_with_expired_invitation(client, db):
    """Registration with expired invitation token fails."""
    admin = await create_user(client, "admin@example.com", "password123", "Admin")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    # Manually create expired invitation
    expired_invite = Invitation(
        token=str(uuid4()),
        email="candidate@example.com",
        role_id=candidate_role.id,
        created_by=admin["id"],
        used=False,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    db.add(expired_invite)
    await db.commit()

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate User",
            "invitation_token": expired_invite.token,
        },
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_invitations_admin_sees_all(client, db):
    """Admin can see all invitations, methodist sees only own."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    # Admin creates invitation
    await client.post(
        "/api/v1/invitations/",
        json={
            "email": "c1@example.com",
            "role_id": str(candidate_role.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Admin list
    response = await client.get(
        "/api/v1/invitations/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_delete_invitation(client, db):
    """Admin can delete an invitation."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "c1@example.com",
            "role_id": str(candidate_role.id),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_id = response.json()["id"]

    response = await client.delete(
        f"/api/v1/invitations/{invite_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(
        "/api/v1/invitations/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_list_invitations_with_null_created_by(client, db):
    """Listing invitations with created_by=None must not raise 500."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    role_result = await db.execute(Role.__table__.select().where(Role.name == UserRole.CANDIDATE))
    candidate_role = role_result.fetchone()

    # Create invitation without created_by (simulating ON DELETE SET NULL)
    orphan_invite = Invitation(
        token=str(uuid4()),
        email="orphan@example.com",
        role_id=candidate_role.id,
        created_by=None,
        used=False,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(orphan_invite)
    await db.commit()

    response = await client.get(
        "/api/v1/invitations/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["created_by"] is None
