"""Tests for module endpoints."""

from uuid import uuid4

import pytest

from tests.conftest import (
    ADMIN_ID,
    METHODIST_1_ID,
    METHODIST_2_ID,
    create_module,
)

# ------------------------------------------------------------------
# POST /modules
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_module_happy(client, admin_headers):
    response = await client.post(
        "/api/v1/modules",
        json={"title": "New Module", "description": "Desc"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Module"
    assert data["description"] == "Desc"
    assert data["status"] == "draft"
    assert data["author_id"] == str(ADMIN_ID)
    assert data["manager_id"] == str(ADMIN_ID)


@pytest.mark.asyncio
async def test_create_module_as_methodist(client, methodist1_headers):
    response = await client.post(
        "/api/v1/modules",
        json={"title": "Methodist Module"},
        headers=methodist1_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["author_id"] == str(METHODIST_1_ID)
    assert data["manager_id"] == str(METHODIST_1_ID)


@pytest.mark.asyncio
async def test_create_module_unauthorized(client):
    response = await client.post("/api/v1/modules", json={"title": "New Module"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_module_forbidden(client, seminarist_headers, candidate_headers):
    for token in [seminarist_headers, candidate_headers]:
        response = await client.post(
            "/api/v1/modules",
            json={"title": "New Module"},
            headers=token,
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_module_invalid(client, admin_headers):
    response = await client.post(
        "/api/v1/modules",
        json={"description": "Missing title"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /modules
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_modules_admin(client, admin_headers, db):
    await create_module(db, title="M1", status="draft", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_module(
        db, title="M2", status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )

    response = await client.get(
        "/api/v1/modules",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_modules_methodist_isolation(client, methodist1_headers, methodist2_headers, db):
    await create_module(db, title="M1", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    await create_module(db, title="M2", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)

    response = await client.get(
        "/api/v1/modules",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "M1"


@pytest.mark.asyncio
async def test_list_modules_seminarist_candidate_only_published(
    client, seminarist_headers, candidate_headers, db
):
    await create_module(
        db, title="Draft", status="draft", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await create_module(
        db,
        title="Published",
        status="published",
        author_id=METHODIST_1_ID,
        manager_id=METHODIST_1_ID,
    )

    for token in [seminarist_headers, candidate_headers]:
        response = await client.get(
            "/api/v1/modules",
            headers=token,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Published"


@pytest.mark.asyncio
async def test_list_modules_pagination(client, admin_headers, db):
    for i in range(5):
        await create_module(db, title=f"M{i}", author_id=ADMIN_ID, manager_id=ADMIN_ID)

    response = await client.get(
        "/api/v1/modules?page=1&size=2",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2

    response = await client.get(
        "/api/v1/modules?page=2&size=2",
        headers=admin_headers,
    )
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_modules_status_filter(client, admin_headers, db):
    await create_module(db, title="Draft", status="draft", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_module(
        db, title="Published", status="published", author_id=ADMIN_ID, manager_id=ADMIN_ID
    )

    response = await client.get(
        "/api/v1/modules?status=published",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Published"


@pytest.mark.asyncio
async def test_list_modules_unauthorized(client):
    response = await client.get("/api/v1/modules")
    assert response.status_code == 401


# ------------------------------------------------------------------
# GET /modules/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_module_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(module_id)


@pytest.mark.asyncio
async def test_get_module_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_module_methodist_other_forbidden(
    client, methodist1_headers, methodist2_headers, db
):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_module_seminarist_published(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_module_seminarist_draft_forbidden(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="draft", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_module_seminarist_wrong_manager(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_module_candidate_published(client, candidate_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=candidate_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/v1/modules/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_module_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.get(f"/api/v1/modules/{module_id}")
    assert response.status_code == 401


# ------------------------------------------------------------------
# PATCH /modules/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_module_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": "Updated Title"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_module_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": "Updated"},
        headers=methodist1_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_module_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": "Updated"},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_module_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": "Updated"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/modules/{fake_id}",
        json={"title": "Updated"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_module_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": 123},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# PATCH /modules/{id}/status
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_module_status_draft_to_published(client, admin_headers, db):
    module_id = await create_module(db, status="draft", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}/status",
        json={"status": "published"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "published"


@pytest.mark.asyncio
async def test_update_module_status_published_to_draft_conflict(client, admin_headers, db):
    module_id = await create_module(db, status="published", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}/status",
        json={"status": "draft"},
        headers=admin_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_module_status_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.patch(
        f"/api/v1/modules/{module_id}/status",
        json={"status": "published"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_module_status_forbidden(client, seminarist_headers, db):
    module_id = await create_module(db)
    response = await client.patch(
        f"/api/v1/modules/{module_id}/status",
        json={"status": "published"},
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_module_status_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/modules/{fake_id}/status",
        json={"status": "published"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_module_status_missing_body(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.patch(
        f"/api/v1/modules/{module_id}/status",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# DELETE /modules/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_module_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.delete(
        f"/api/v1/modules/{module_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    # Verify gone
    get_resp = await client.get(
        f"/api/v1/modules/{module_id}",
        headers=admin_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_module_methodist_draft(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="draft", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.delete(
        f"/api/v1/modules/{module_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_module_methodist_published_conflict(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.delete(
        f"/api/v1/modules/{module_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_module_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="draft", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    response = await client.delete(
        f"/api/v1/modules/{module_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_module_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.delete(f"/api/v1/modules/{module_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/modules/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404
