"""Tests for /api/v1/tests endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import METHODIST_2_ID, create_question, create_test

# ------------------------------------------------------------------
# POST /api/v1/tests
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_test_success(
    client: AsyncClient,
    methodist1_headers: dict,
) -> None:
    """Methodist can create a test."""
    response = await client.post(
        "/api/v1/tests",
        headers=methodist1_headers,
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
    seminarist_headers: dict,
) -> None:
    """Seminarist cannot create a test."""
    response = await client.post(
        "/api/v1/tests",
        headers=seminarist_headers,
        json={"module_id": str(uuid4()), "title": "Test"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_test_invalid_body(
    client: AsyncClient,
    methodist1_headers: dict,
) -> None:
    """Invalid body returns 422."""
    response = await client.post(
        "/api/v1/tests",
        headers=methodist1_headers,
        json={"title": "Test"},  # missing module_id
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /api/v1/tests
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_tests_methodist(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist sees only own tests."""
    await create_test(db, title="Methodist Test")

    response = await client.get(
        "/api/v1/tests",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Methodist Test"


@pytest.mark.anyio
async def test_list_tests_seminarist(
    client: AsyncClient,
    seminarist_headers: dict,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Seminarist sees only active tests of their manager."""
    await create_test(db, title="Active Test", is_active=True)
    await create_test(db, title="Inactive Test", is_active=False)

    response = await client.get(
        "/api/v1/tests",
        headers=seminarist_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Active Test"


@pytest.mark.anyio
async def test_list_tests_methodist_with_module_id(
    client: AsyncClient,
    methodist1_headers: dict,
    methodist2_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist sees all tests for a specific module_id."""
    module_id = uuid4()
    await create_test(db, title="Test 1", module_id=module_id)
    await create_test(db, title="Test 2", module_id=module_id, is_active=False)

    response = await client.get(
        f"/api/v1/tests?module_id={module_id}",
        headers=methodist2_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    titles = {item["title"] for item in data["items"]}
    assert titles == {"Test 1", "Test 2"}


@pytest.mark.anyio
async def test_list_tests_methodist_without_module_id(
    client: AsyncClient,
    methodist1_headers: dict,
    methodist2_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist sees only own tests when no module_id is provided."""
    await create_test(db, title="Own Test")

    response = await client.get(
        "/api/v1/tests",
        headers=methodist2_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.anyio
async def test_list_tests_unauthorized(client: AsyncClient) -> None:
    """Listing tests without token returns 401."""
    response = await client.get("/api/v1/tests")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_tests_admin(
    client: AsyncClient,
    admin_headers: dict,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Admin sees all tests."""
    await create_test(db, title="Admin Test 1")
    await create_test(db, title="Admin Test 2")

    response = await client.get(
        "/api/v1/tests",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.anyio
async def test_list_tests_candidate_inactive_hidden(
    client: AsyncClient,
    candidate_headers: dict,
    db: AsyncSession,
) -> None:
    """Candidate does not see inactive tests."""
    await create_test(db, title="Inactive Test", is_active=False)

    response = await client.get(
        "/api/v1/tests",
        headers=candidate_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.anyio
async def test_list_tests_candidate_sees_all_active(
    client: AsyncClient,
    candidate_headers: dict,
    db: AsyncSession,
) -> None:
    """Candidate sees all active tests regardless of manager."""
    await create_test(db, title="Active Test", is_active=True, manager_id=METHODIST_2_ID)

    response = await client.get(
        "/api/v1/tests",
        headers=candidate_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Active Test"


# ------------------------------------------------------------------
# GET /api/v1/tests/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_test_success(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can get their own test."""
    test_id = await create_test(db, title="My Test")

    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Test"


@pytest.mark.anyio
async def test_get_test_question_count(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """GET test returns correct question_count when questions exist."""
    test_id = await create_test(db, title="Test with questions")
    await create_question(db, test_id)
    await create_question(db, test_id)

    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question_count"] == 2


@pytest.mark.anyio
async def test_list_tests_question_count(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """LIST tests returns correct question_count for each test."""
    test1_id = await create_test(db, title="Test 1")
    await create_question(db, test1_id)
    test2_id = await create_test(db, title="Test 2")
    await create_question(db, test2_id)
    await create_question(db, test2_id)

    response = await client.get(
        "/api/v1/tests",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) == 2
    counts = {item["title"]: item["question_count"] for item in items}
    assert counts["Test 1"] == 1
    assert counts["Test 2"] == 2


@pytest.mark.anyio
async def test_get_test_not_found(
    client: AsyncClient,
    methodist1_headers: dict,
) -> None:
    """Getting non-existent test returns 404."""
    response = await client.get(
        f"/api/v1/tests/{uuid4()}",
        headers=methodist1_headers,
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_test_other_methodist_allowed(
    client: AsyncClient,
    methodist1_headers: dict,
    methodist2_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can read another methodist's test (read-only)."""
    test_id = await create_test(db, title="Other Test")

    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers=methodist2_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Other Test"


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
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can update their own test."""
    test_id = await create_test(db, title="Old Title")

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"


@pytest.mark.anyio
async def test_update_test_not_found(
    client: AsyncClient,
    methodist1_headers: dict,
) -> None:
    """Updating non-existent test returns 404."""
    response = await client.patch(
        f"/api/v1/tests/{uuid4()}",
        headers=methodist1_headers,
        json={"title": "New Title"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_test_forbidden(
    client: AsyncClient,
    methodist2_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist cannot update another methodist's test."""
    test_id = await create_test(db, title="Other Test")

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist2_headers,
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
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Invalid body returns 422."""
    test_id = await create_test(db)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"pass_score": "not_a_number"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_test_pass_score_boundary(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Pass score boundaries 0 and 100 are accepted."""
    test_id = await create_test(db, pass_score=50)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"pass_score": 0},
    )
    assert response.status_code == 200
    assert response.json()["pass_score"] == 0

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"pass_score": 100},
    )
    assert response.status_code == 200
    assert response.json()["pass_score"] == 100


@pytest.mark.anyio
async def test_update_test_pass_score_out_of_range(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Pass score outside 0-100 returns 422."""
    test_id = await create_test(db)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"pass_score": 101},
    )
    assert response.status_code == 422

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"pass_score": -1},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_test_module_id(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can change test module_id."""
    test_id = await create_test(db, title="Module Change")
    new_module_id = str(uuid4())

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"module_id": new_module_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["module_id"] == new_module_id


@pytest.mark.anyio
async def test_update_test_deactivate(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can deactivate and reactivate a test."""
    test_id = await create_test(db, title="Toggle Active", is_active=True)

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"is_active": False},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    response = await client.patch(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
        json={"is_active": True},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


# ------------------------------------------------------------------
# DELETE /api/v1/tests/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_test_success(
    client: AsyncClient,
    methodist1_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist can delete their own test."""
    test_id = await create_test(db, title="To Delete")

    response = await client.delete(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(
        f"/api/v1/tests/{test_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_test_not_found(
    client: AsyncClient,
    methodist1_headers: dict,
) -> None:
    """Deleting non-existent test returns 404."""
    response = await client.delete(
        f"/api/v1/tests/{uuid4()}",
        headers=methodist1_headers,
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_test_forbidden(
    client: AsyncClient,
    methodist2_headers: dict,
    db: AsyncSession,
) -> None:
    """Methodist cannot delete another methodist's test."""
    test_id = await create_test(db, title="Other Test")

    response = await client.delete(
        f"/api/v1/tests/{test_id}",
        headers=methodist2_headers,
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_delete_test_unauthorized(client: AsyncClient) -> None:
    """Deleting test without token returns 401."""
    response = await client.delete(f"/api/v1/tests/{uuid4()}")
    assert response.status_code == 401
