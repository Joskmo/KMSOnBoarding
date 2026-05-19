import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test registration with duplicate email returns 400."""
    await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User 2"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login(client):
    """Test successful login returns tokens."""
    await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })
    response = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials returns 401."""
    response = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Test accessing /me without token returns 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authorized(client):
    """Test accessing /me with valid token returns user data."""
    await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })
    login_response = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    response = await client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
