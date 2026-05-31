"""Tests for module assignment endpoints."""

import pytest

from tests.conftest import (
    ADMIN_ID,
    CANDIDATE_ID,
    METHODIST_1_ID,
    METHODIST_2_ID,
    SEMINARIST_ID,
    assign_module,
    create_module,
)

# ------------------------------------------------------------------
# POST /modules/{id}/assignments
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_assignments_admin(client, admin_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID)]},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["module_id"] == str(module_id)
    assert data[0]["user_id"] == str(SEMINARIST_ID)


@pytest.mark.asyncio
async def test_create_assignments_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID), str(CANDIDATE_ID)]},
        headers=methodist1_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_assignments_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID)]},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_assignments_draft_module(client, admin_headers, db):
    module_id = await create_module(db, status="draft", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID)]},
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_assignments_idempotent(client, admin_headers, db):
    module_id = await create_module(db, status="published", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    # First call
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID)]},
        headers=admin_headers,
    )
    assert response.status_code == 201
    # Second call — should not error or duplicate
    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(SEMINARIST_ID)]},
        headers=admin_headers,
    )
    assert response.status_code == 201
    # Verify only one assignment exists
    list_resp = await client.get(
        f"/api/v1/modules/{module_id}/assignments",
        headers=admin_headers,
    )
    assert len(list_resp.json()) == 1


# ------------------------------------------------------------------
# DELETE /modules/{id}/assignments/{user_id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_assignment_admin(client, admin_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await assign_module(db, module_id=module_id, user_id=SEMINARIST_ID)

    response = await client.delete(
        f"/api/v1/modules/{module_id}/assignments/{SEMINARIST_ID}",
        headers=admin_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_assignment_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await assign_module(db, module_id=module_id, user_id=SEMINARIST_ID)

    response = await client.delete(
        f"/api/v1/modules/{module_id}/assignments/{SEMINARIST_ID}",
        headers=methodist1_headers,
    )
    assert response.status_code == 204


# ------------------------------------------------------------------
# GET /modules/{id}/assignments
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_assignments(client, admin_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await assign_module(db, module_id=module_id, user_id=SEMINARIST_ID)
    await assign_module(db, module_id=module_id, user_id=CANDIDATE_ID)

    response = await client.get(
        f"/api/v1/modules/{module_id}/assignments",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ------------------------------------------------------------------
# RBAC: seminarist/candidate only sees assigned modules
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_modules_seminarist_no_assignment(client, seminarist_headers, db):
    await create_module(
        db,
        title="Published",
        status="published",
        author_id=METHODIST_1_ID,
        manager_id=METHODIST_1_ID,
    )
    response = await client.get("/api/v1/modules", headers=seminarist_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_module_seminarist_not_assigned(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_lessons_seminarist_not_assigned(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_heuristics_seminarist_not_assigned(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


# ------------------------------------------------------------------
# Cleanup endpoint
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_assignments_by_user_admin(client, admin_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await assign_module(db, module_id=module_id, user_id=SEMINARIST_ID)

    response = await client.delete(
        f"/api/v1/module-assignments/user/{SEMINARIST_ID}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    # Verify assignments are gone
    list_resp = await client.get(
        f"/api/v1/modules/{module_id}/assignments",
        headers=admin_headers,
    )
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_cleanup_assignments_by_user_forbidden(client, methodist1_headers):
    response = await client.delete(
        f"/api/v1/module-assignments/user/{SEMINARIST_ID}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403
