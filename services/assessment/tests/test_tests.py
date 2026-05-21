"""Tests for /api/v1/tests endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import METHODIST_2_ID, create_test

# ------------------------------------------------------------------
# POST /api/v1/tests
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_test_success(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Methodist can create a test."""
    response = await client.post(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={
            "module_id": str(uuid4()),
            "title": "Regression Test",
            "description": "Check knowledge",
            "pass_score": 75,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Regression Test"
    assert data["pass_score"] == 75
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_create_test_unauthorized(client: AsyncClient) -> None:
    """Creating a test without token returns 401."""
    response = await client.post(
        "/api/v1/tests",
        json={"module_id": str(uuid4()), "title": "Test"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_test_forbidden(
    client: AsyncClient,
    seminarist_token: str,
) -> None:
    """Seminarist cannot create a test."""
    response = await client.post(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"module_id": str(uuid4()), "title": "Test"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_test_invalid_body(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Invalid body returns 422."""
    response = await client.post(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"title": "Test"},  # missing module_id
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /api/v1/tests
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_tests_methodist(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist sees only own tests."""
    await create_test(db, title="Methodist Test")

    response = await client.get(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Methodist Test"


@pytest.mark.anyio
async def test_list_tests_seminarist(
    client: AsyncClient,
    seminarist_token: str,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Seminarist sees only active tests of their manager."""
    await create_test(db, title="Active Test", is_active=True)
    await create_test(db, title="Inactive Test", is_active=False)

    response = await client.get(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Active Test"


@pytest.mark.anyio
async def test_list_tests_unauthorized(client: AsyncClient) -> None:
    """Listing tests without token returns 401."""
    response = await client.get("/api/v1/tests")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_tests_admin(
    client: AsyncClient,
    admin_token: str,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Admin sees all tests."""
    await create_test(db, title="Admin Test 1")
    await create_test(db, title="Admin Test 2")

    response = await client.get(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.anyio
async def test_list_tests_candidate_other_manager(
    client: AsyncClient,
    candidate_token: str,
    db: AsyncSession,
) -> None:
    """Candidate does not see tests of another manager."""
    await create_test(db, title="Other Manager", is_active=True, manager_id=METHODIST_2_ID)

    response = await client.get(
        "/api/v1/tests",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


# ------------------------------------------------------------------
# GET /api/v1/tests/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_test_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can get their own test."""
    test_id = await create_test(db, title="My Test")

    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Test"


@pytest.mark.anyio
async def test_get_test_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Getting non-existent test returns 404."""
    response = await client.get(
        f"/api/v1/tests/{uuid4()}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_test_forbidden(
    client: AsyncClient,
    methodist1_token: str,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot get another methodist's test."""
    test_id = await create_test(db, title="Other Test")

    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_test_unauthorized(client: AsyncClient) -> None:
    """Getting test without token returns 401."""
    response = await client.get(f"/api/v1/tests/{uuid4()}")
    assert response.status_code == 401


# ------------------------------------------------------------------
# PATCH /api/v1/tests/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_update_test_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can update their own test."""
    test_id = await create_test(db, title="Old Title")

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"


@pytest.mark.anyio
async def test_update_test_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Updating non-existent test returns 404."""
    response = await client.patch(
        f"/api/v1/tests/{uuid4()}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"title": "New Title"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_test_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot update another methodist's test."""
    test_id = await create_test(db, title="Other Test")

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
        json={"title": "New Title"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_test_unauthorized(client: AsyncClient) -> None:
    """Updating test without token returns 401."""
    response = await client.patch(
        f"/api/v1/tests/{uuid4()}",
        json={"title": "New Title"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_test_invalid_body(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Invalid body returns 422."""
    test_id = await create_test(db)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"pass_score": "not_a_number"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_test_pass_score_boundary(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Pass score boundaries 0 and 100 are accepted."""
    test_id = await create_test(db, pass_score=50)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"pass_score": 0},
    )
    assert response.status_code == 200
    assert response.json()["pass_score"] == 0

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"pass_score": 100},
    )
    assert response.status_code == 200
    assert response.json()["pass_score"] == 100


@pytest.mark.anyio
async def test_update_test_pass_score_out_of_range(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Pass score outside 0-100 returns 422."""
    test_id = await create_test(db)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"pass_score": 101},
    )
    assert response.status_code == 422

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"pass_score": -1},
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# DELETE /api/v1/tests/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_test_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can delete their own test."""
    test_id = await create_test(db, title="To Delete")

    response = await client.delete(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_test_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Deleting non-existent test returns 404."""
    response = await client.delete(
        f"/api/v1/tests/{uuid4()}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_test_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot delete another methodist's test."""
    test_id = await create_test(db, title="Other Test")

    response = await client.delete(
        f"/api/v1/tests/{test_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_delete_test_unauthorized(client: AsyncClient) -> None:
    """Deleting test without token returns 401."""
    response = await client.delete(f"/api/v1/tests/{uuid4()}")
    assert response.status_code == 401
