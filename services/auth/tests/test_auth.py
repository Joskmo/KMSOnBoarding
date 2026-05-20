from uuid import uuid4

import pytest

from app.core.enums import UserRole


@pytest.mark.asyncio
async def test_register_first_user_becomes_admin(client):
    """Test first registered user gets admin role."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@example.com"
    assert data["full_name"] == "Admin User"
    assert "id" in data
    # Check role
    assert data["role"] == UserRole.ADMIN


@pytest.mark.asyncio
async def test_register_second_user_requires_invitation(client):
    """Test second user registration requires invitation token."""
    # First user (admin)
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin User"},
    )
    # Second user without invitation
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert response.status_code == 400
    assert "invitation" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test registration with duplicate email returns 400."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User 2"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login(client):
    """Test successful login returns tokens."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials returns 401."""
    response = await client.post(
        "/api/v1/auth/login", data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client):
    """Test registration with password < 8 chars returns 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "my_pass",
            "full_name": "Admin User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Test accessing /me without token returns 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authorized(client):
    """Test accessing /me with valid token returns user data."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    login_response = await client.post(
        "/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_methodist_can_get_own_profile(client):
    """Methodist should be able to view their own profile."""
    # Register admin first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Admin creates invitation for methodist
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = invite_resp.json()["token"]

    # Methodist registers
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": invite_token,
        },
    )
    methodist_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "methodist@example.com", "password": "password123"},
    )
    methodist_token = methodist_login.json()["access_token"]

    # Get methodist ID from /me
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    methodist_id = me_resp.json()["id"]

    # Methodist gets own profile
    response = await client.get(
        f"/api/v1/users/{methodist_id}",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "methodist@example.com"
    assert data["role"] == "methodist"


@pytest.mark.asyncio
async def test_methodist_can_update_own_profile(client):
    """Methodist should be able to update their own profile."""
    # Register admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Create and register methodist
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = invite_resp.json()["token"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": invite_token,
        },
    )
    methodist_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "methodist@example.com", "password": "password123"},
    )
    methodist_token = methodist_login.json()["access_token"]

    # Get methodist ID from /me
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    methodist_id = me_resp.json()["id"]

    # Methodist updates own full_name
    response = await client.put(
        f"/api/v1/users/{methodist_id}",
        json={"full_name": "Updated Methodist"},
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Methodist"


@pytest.mark.asyncio
async def test_methodist_list_includes_self(client):
    """Methodist user list should include themselves."""
    # Register admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Create and register methodist
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = invite_resp.json()["token"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": invite_token,
        },
    )
    methodist_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "methodist@example.com", "password": "password123"},
    )
    methodist_token = methodist_login.json()["access_token"]

    # Methodist lists users - should see themselves even with no subordinates
    response = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "methodist@example.com"
    assert data[0]["role"] == "methodist"


@pytest.mark.asyncio
async def test_admin_can_delete_user(client):
    """Admin can delete a user without subordinates."""
    # Create admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Create methodist via invitation
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    invite_token = invite_resp.json()["token"]

    methodist_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": invite_token,
        },
    )
    methodist_id = methodist_reg.json()["id"]

    # Admin deletes methodist
    response = await client.delete(
        f"/api/v1/users/{methodist_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204

    # Verify user is gone
    get_resp = await client.get(
        f"/api/v1/users/{methodist_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_cannot_delete_user_with_subordinates(client):
    """Admin cannot delete a user who has active subordinates."""
    # Create admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Create methodist
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    methodist_token = invite_resp.json()["token"]
    methodist_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": methodist_token,
        },
    )
    methodist_id = methodist_reg.json()["id"]

    # Methodist logs in and creates candidate invitation (auto-assigns self as manager)
    methodist_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "methodist@example.com", "password": "password123"},
    )
    methodist_auth_token = methodist_login.json()["access_token"]

    candidate_invite = await client.post(
        "/api/v1/invitations/",
        json={"email": "candidate@example.com", "role_name": "candidate"},
        headers={"Authorization": f"Bearer {methodist_auth_token}"},
    )
    candidate_token = candidate_invite.json()["token"]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate",
            "invitation_token": candidate_token,
        },
    )

    # Try to delete methodist who has subordinate
    response = await client.delete(
        f"/api/v1/users/{methodist_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "subordinates" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_non_admin_cannot_delete_user(client):
    """Non-admin user cannot delete other users."""
    # Create admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    # Create methodist
    invite_resp = await client.post(
        "/api/v1/invitations/",
        json={"email": "methodist@example.com", "role_name": "methodist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    methodist_invite_token = invite_resp.json()["token"]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "methodist@example.com",
            "password": "password123",
            "full_name": "Methodist",
            "invitation_token": methodist_invite_token,
        },
    )
    methodist_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "methodist@example.com", "password": "password123"},
    )
    methodist_token = methodist_login.json()["access_token"]

    # Create another user (candidate) for methodist to try to delete
    candidate_invite = await client.post(
        "/api/v1/invitations/",
        json={"email": "candidate@example.com", "role_name": "candidate"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    candidate_token = candidate_invite.json()["token"]
    candidate_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "candidate@example.com",
            "password": "password123",
            "full_name": "Candidate",
            "invitation_token": candidate_token,
        },
    )
    candidate_id = candidate_reg.json()["id"]

    # Methodist tries to delete candidate
    response = await client.delete(
        f"/api/v1/users/{candidate_id}",
        headers={"Authorization": f"Bearer {methodist_token}"},
    )
    assert response.status_code == 403
    assert "only admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_nonexistent_user(client):
    """Deleting a nonexistent user returns 404."""
    # Create admin
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login", data={"username": "admin@example.com", "password": "password123"}
    )
    admin_token = admin_login.json()["access_token"]

    fake_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/users/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
