from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.enums import UserRole
from app.db.models import Invitation


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
async def test_admin_can_create_invitation_for_any_role(client):
    """Admin can create invitation for methodist role."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "new@example.com",
            "role_name": UserRole.METHODIST,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["used"] is False
    assert "token" in data


@pytest.mark.asyncio
async def test_methodist_can_create_invitation_for_candidate(client):
    """Methodist can create invitation for candidate."""
    # Create admin first to invite methodist
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin invites methodist
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "methodist@example.com",
            "role_name": UserRole.METHODIST,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    # Methodist registers
    _ = await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=invite_token,
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    # Methodist invites candidate
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {methodist_token}"},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_methodist_cannot_create_invitation_for_admin(client):
    """Methodist cannot create invitation for admin role."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "methodist@example.com",
            "role_name": UserRole.METHODIST,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=invite_token,
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "new_admin@example.com",
            "role_name": UserRole.ADMIN,
        },
        headers={"Authorization": f"Bearer {methodist_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_with_valid_invitation(client):
    """User can register with a valid invitation token."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
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
    assert data["role"] == UserRole.CANDIDATE


@pytest.mark.asyncio
async def test_register_with_used_invitation(client):
    """Registration with used invitation token fails."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
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

    # Manually create expired invitation
    expired_invite = Invitation(
        token=str(uuid4()),
        email="candidate@example.com",
        role_name=UserRole.CANDIDATE,
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
async def test_list_invitations_admin_sees_all(client):
    """Admin can see all invitations, methodist sees only own."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin creates invitation
    await client.post(
        "/api/v1/invitations/",
        json={
            "email": "c1@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Admin list
    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_delete_invitation(client):
    """Admin can delete an invitation."""
    _ = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "c1@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_id = response.json()["id"]

    response = await client.delete(
        f"/api/v1/invitations/{invite_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_list_invitations_with_null_created_by(client, db):
    """Listing invitations with created_by=None must not raise 500."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Create invitation without created_by (simulating ON DELETE SET NULL)
    orphan_invite = Invitation(
        token=str(uuid4()),
        email="orphan@example.com",
        role_name=UserRole.CANDIDATE,
        created_by=None,
        used=False,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(orphan_invite)
    await db.commit()

    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["created_by"] is None


@pytest.mark.asyncio
async def test_candidate_cannot_create_invitation(client):
    """Candidate gets 403 when trying to create an invitation."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    await create_user(
        client,
        "candidate@example.com",
        "password123",
        "Candidate",
        invitation_token=invite_token,
    )
    candidate_token = await login_user(client, "candidate@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "new@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_invitation_for_existing_user_email(client):
    """Creating invitation for an already registered email returns 422."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "admin@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_invitation_idempotent(client):
    """Creating invitation for same active email returns existing invitation."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # First invitation
    response1 = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "dup@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response1.status_code == 201
    token1 = response1.json()["token"]

    # Second invitation for same email — should return existing
    response2 = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "dup@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response2.status_code == 201
    assert response2.json()["token"] == token1


@pytest.mark.asyncio
async def test_register_with_wrong_email_for_invitation(client):
    """Registration with email different from invitation email returns 400."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "specific@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "password123",
            "full_name": "Wrong Email",
            "invitation_token": invite_token,
        },
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_with_matching_email_for_invitation(client):
    """Registration with matching invitation email succeeds."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "match@example.com",
            "role_name": UserRole.CANDIDATE,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "match@example.com",
            "password": "password123",
            "full_name": "Matching Email",
            "invitation_token": invite_token,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "match@example.com"
    assert data["role"] == UserRole.CANDIDATE


@pytest.mark.asyncio
async def test_seminarist_cannot_list_invitations(client):
    """Seminarist gets 403 when trying to list invitations."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "seminarist@example.com",
            "role_name": UserRole.SEMINARIST,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    await create_user(
        client,
        "seminarist@example.com",
        "password123",
        "Seminarist",
        invitation_token=invite_token,
    )
    seminarist_token = await login_user(client, "seminarist@example.com", "password123")

    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_methodist_sees_only_own_invitations(client):
    """Methodist should see only invitations they created."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Invite methodist1
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m1@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token1 = response.json()["token"]

    # Invite methodist2
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m2@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token2 = response.json()["token"]

    await create_user(client, "m1@example.com", "password123", "M1", invitation_token=token1)
    m1_token = await login_user(client, "m1@example.com", "password123")

    await create_user(client, "m2@example.com", "password123", "M2", invitation_token=token2)
    m2_token = await login_user(client, "m2@example.com", "password123")

    # M1 creates invitation
    await client.post(
        "/api/v1/invitations/",
        json={"email": "c1@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {m1_token}"},
    )

    # M2 creates invitation
    await client.post(
        "/api/v1/invitations/",
        json={"email": "c2@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {m2_token}"},
    )

    # M1 should see only 1
    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {m1_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "c1@example.com"


@pytest.mark.asyncio
async def test_methodist_can_delete_own_invitation(client):
    """Methodist can delete their own invitation."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "methodist@example.com",
            "role_name": UserRole.METHODIST,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=invite_token,
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "c1@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    invite_id = response.json()["id"]

    response = await client.delete(
        f"/api/v1/invitations/{invite_id}",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_methodist_cannot_delete_others_invitation(client):
    """Methodist cannot delete an invitation created by another user."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Invite m1
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m1@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token1 = response.json()["token"]

    # Invite m2
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m2@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token2 = response.json()["token"]

    await create_user(client, "m1@example.com", "password123", "M1", invitation_token=token1)
    m1_token = await login_user(client, "m1@example.com", "password123")

    await create_user(client, "m2@example.com", "password123", "M2", invitation_token=token2)
    m2_token = await login_user(client, "m2@example.com", "password123")

    # M1 creates invitation
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "c1@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {m1_token}"},
    )
    invite_id = response.json()["id"]

    # M2 tries to delete M1's invitation
    response = await client.delete(
        f"/api/v1/invitations/{invite_id}",
        headers={"Authorization": f"Bearer {m2_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_nonexistent_invitation(client):
    """Deleting a nonexistent invitation returns 404."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    fake_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/invitations/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_invitation_with_invalid_role_name(client):
    """Creating invitation with invalid role_name returns 422."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "new@example.com", "role_name": "superuser"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_with_invalid_invitation_token(client):
    """Registration with a random invalid token returns 400."""
    # Ensure at least one user exists so this is not treated as first-user registration
    await create_user(client, "admin@example.com", "password123", "Admin")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "User",
            "invitation_token": str(uuid4()),
        },
    )
    assert response.status_code == 400
    assert "Invalid invitation token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_methodist_auto_assigns_manager_id(client):
    """Methodist creating candidate invitation without manager_id auto-assigns self."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin invites methodist
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    methodist = await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=invite_token,
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    # Methodist invites candidate without specifying manager_id
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "candidate@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["manager_id"] == methodist["id"]


@pytest.mark.asyncio
async def test_methodist_cannot_assign_other_manager(client):
    """Methodist cannot assign another user as manager for subordinate."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Invite methodist1
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m1@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    token1 = response.json()["token"]

    # Invite methodist2
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "m2@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    m2 = await create_user(
        client, "m2@example.com", "password123", "M2", invitation_token=response.json()["token"]
    )

    await create_user(client, "m1@example.com", "password123", "M1", invitation_token=token1)
    m1_token = await login_user(client, "m1@example.com", "password123")

    # M1 tries to assign M2 as manager
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
            "manager_id": str(m2["id"]),
        },
        headers={"Authorization": f"Bearer {m1_token}"},
    )
    assert response.status_code == 422
    assert "Methodist can only assign subordinates to themselves" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_assign_methodist_as_manager(client):
    """Admin can assign a methodist as manager when creating invitation."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Invite methodist
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    methodist = await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=response.json()["token"],
    )

    # Admin creates candidate invitation with methodist as manager
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "candidate@example.com",
            "role_name": UserRole.CANDIDATE,
            "manager_id": str(methodist["id"]),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["manager_id"] == methodist["id"]


@pytest.mark.asyncio
async def test_methodist_invitation_for_methodist_no_manager(client):
    """Methodist invitation always has null manager_id even if specified."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin invites a methodist
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": UserRole.METHODIST},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    methodist = await create_user(
        client,
        "methodist@example.com",
        "password123",
        "Methodist",
        invitation_token=response.json()["token"],
    )
    methodist_token = await login_user(client, "methodist@example.com", "password123")

    # Methodist invites another methodist with manager_id — should be ignored
    response = await client.post(
        "/api/v1/invitations/",
        json={
            "email": "m2@example.com",
            "role_name": UserRole.METHODIST,
            "manager_id": str(methodist["id"]),
        },
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 201
    assert response.json()["manager_id"] is None


@pytest.mark.asyncio
async def test_admin_auto_assigns_self_as_manager(client):
    """Admin creating candidate invitation without manager_id auto-assigns self."""
    admin = await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin creates candidate invitation without specifying manager_id
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "candidate@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["manager_id"] == admin["id"]


@pytest.mark.asyncio
async def test_invitation_used_by_set_after_registration(client):
    """After registration invitation.used_by must contain the new user ID."""
    await create_user(client, "admin@example.com", "password123", "Admin")
    admin_token = await login_user(client, "admin@example.com", "password123")

    # Admin creates invitation
    response = await client.post(
        "/api/v1/invitations/",
        json={"email": "candidate@example.com", "role_name": UserRole.CANDIDATE},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = response.json()["token"]

    # Register with the invitation
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate",
            "invitation_token": invite_token,
        },
    )
    assert reg_response.status_code == 201
    new_user_id = reg_response.json()["id"]

    # Verify invitation shows used_by
    response = await client.get(
        "/api/v1/invitations/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    invites = response.json()
    assert len(invites) == 1
    assert invites[0]["used"] is True
    assert invites[0]["used_by"] == new_user_id
