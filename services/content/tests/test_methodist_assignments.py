"""Tests for methodist viewing assigned modules."""

import pytest

from tests.conftest import (
    METHODIST_1_ID,
    METHODIST_2_ID,
    assign_module,
    create_module,
)


@pytest.mark.asyncio
async def test_list_modules_methodist_sees_own_and_assigned(
    client, methodist1_headers, methodist2_headers, db
):
    own_id = await create_module(
        db, title="Own", status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    other_id = await create_module(
        db, title="Other", status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=other_id, user_id=METHODIST_1_ID)

    response = await client.get("/api/v1/modules", headers=methodist1_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    titles = {m["title"] for m in data["items"]}
    assert "Own" in titles
    assert "Other" in titles


@pytest.mark.asyncio
async def test_get_module_methodist_assigned_published(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.get(
        f"/api/v1/modules/{module_id}", headers=methodist1_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_lessons_methodist_assigned(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.get(
        f"/api/v1/modules/{module_id}/lessons", headers=methodist1_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_heuristics_methodist_assigned(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics", headers=methodist1_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_module_methodist_assigned_forbidden(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.patch(
        f"/api/v1/modules/{module_id}",
        json={"title": "Hacked"},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_module_methodist_assigned_forbidden(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="draft", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.delete(
        f"/api/v1/modules/{module_id}", headers=methodist1_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_assignments_methodist_assigned_forbidden(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.post(
        f"/api/v1/modules/{module_id}/assignments",
        json={"user_ids": [str(METHODIST_2_ID)]},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_assignments_methodist_assigned_allowed(
    client, methodist1_headers, db
):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    await assign_module(db, module_id=module_id, user_id=METHODIST_1_ID)

    response = await client.get(
        f"/api/v1/modules/{module_id}/assignments",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert str(data[0]["user_id"]) == str(METHODIST_1_ID)
