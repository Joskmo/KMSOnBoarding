import pytest

@pytest.mark.asyncio
async def test_register_user(client):
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
    response = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_authorized(client):
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
