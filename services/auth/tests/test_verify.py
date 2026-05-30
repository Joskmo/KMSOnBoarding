"""Tests for the /auth/verify endpoint used by API Gateway."""

import pytest


@pytest.mark.asyncio
async def test_verify_valid_token(client):
    """Verify endpoint returns 200 and identity headers for valid token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "x-user-id" in response.headers
    assert response.headers["x-user-role"] == "admin"


@pytest.mark.asyncio
async def test_verify_no_token(client):
    """Verify endpoint returns 401 when no token is provided."""
    response = await client.get("/api/v1/auth/verify")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_invalid_token(client):
    """Verify endpoint returns 401 for malformed token."""
    response = await client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_blacklisted_token(client):
    """Verify endpoint returns 401 after token is revoked via logout."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "full_name": "Admin"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    # Logout revokes the token
    await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Verify should now reject it
    response = await client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
