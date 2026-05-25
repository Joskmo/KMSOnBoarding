"""Tests for heuristic endpoints."""

from uuid import uuid4

import pytest

from tests.conftest import (
    ADMIN_ID,
    CANDIDATE_ID,
    METHODIST_1_ID,
    METHODIST_2_ID,
    SEMINARIST_ID,
    create_heuristic,
    create_module,
)

# ------------------------------------------------------------------
# POST /modules/{id}/heuristics
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_heuristic_admin_any_module(client, admin_headers, db):
    module_id = await create_module(db, status="draft", author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "FAQ entry"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "FAQ entry"
    assert data["author_id"] == str(ADMIN_ID)


@pytest.mark.asyncio
async def test_create_heuristic_seminarist_published(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "Seminarist FAQ"},
        headers=seminarist_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Seminarist FAQ"
    assert data["author_id"] == str(SEMINARIST_ID)
    assert data["manager_id"] == str(METHODIST_1_ID)


@pytest.mark.asyncio
async def test_create_heuristic_candidate_published(client, candidate_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "Candidate FAQ"},
        headers=candidate_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_heuristic_seminarist_unpublished_forbidden(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="draft", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "FAQ"},
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_heuristic_seminarist_wrong_manager(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "FAQ"},
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_heuristic_unauthorized(client, db):
    module_id = await create_module(db, status="published")
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={"content": "FAQ"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_heuristic_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.post(
        f"/api/v1/modules/{fake_id}/heuristics",
        json={"content": "FAQ"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_heuristic_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/heuristics",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /modules/{id}/heuristics
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_heuristics_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_heuristic(db, module_id, content="H1", is_approved=True)
    await create_heuristic(db, module_id, content="H2", is_approved=False)

    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_heuristics_approved_only(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_heuristic(db, module_id, content="H1", is_approved=True)
    await create_heuristic(db, module_id, content="H2", is_approved=False)

    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics?approved_only=true",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "H1"


@pytest.mark.asyncio
async def test_list_heuristics_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.get(f"/api/v1/modules/{module_id}/heuristics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_heuristics_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/v1/modules/{fake_id}/heuristics",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_heuristics_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_heuristics_seminarist_own_unapproved_visible(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    await create_heuristic(db, module_id, content="Own", author_id=SEMINARIST_ID, is_approved=False)
    await create_heuristic(
        db, module_id, content="Other", author_id=CANDIDATE_ID, is_approved=False
    )
    await create_heuristic(
        db, module_id, content="Approved", author_id=CANDIDATE_ID, is_approved=True
    )

    response = await client.get(
        f"/api/v1/modules/{module_id}/heuristics",
        headers=seminarist_headers,
    )
    assert response.status_code == 200
    data = response.json()
    contents = {h["content"] for h in data}
    assert "Own" in contents
    assert "Approved" in contents
    assert "Other" not in contents


# ------------------------------------------------------------------
# GET /heuristics/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_heuristic_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(db, module_id, content="H", is_approved=False)
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "H"


@pytest.mark.asyncio
async def test_get_heuristic_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(db, module_id, content="H")
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_heuristic_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(db, module_id, content="H", manager_id=METHODIST_2_ID)
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_heuristic_seminarist_approved(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(db, module_id, content="H", is_approved=True)
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_heuristic_seminarist_own_unapproved(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="H", author_id=SEMINARIST_ID, is_approved=False
    )
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_heuristic_seminarist_other_unapproved_forbidden(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="H", author_id=CANDIDATE_ID, is_approved=False
    )
    response = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_heuristic_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.get(f"/api/v1/heuristics/{h_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_heuristic_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/v1/heuristics/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


# ------------------------------------------------------------------
# PATCH /heuristics/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_heuristic_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(db, module_id, content="Old")
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": "New"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "New"


@pytest.mark.asyncio
async def test_update_heuristic_author_unapproved(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="Old", author_id=SEMINARIST_ID, is_approved=False
    )
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": "New"},
        headers=seminarist_headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "New"


@pytest.mark.asyncio
async def test_update_heuristic_approved_pending(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="Old", author_id=SEMINARIST_ID, is_approved=True
    )
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": "New"},
        headers=seminarist_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Old"
    assert data["pending_content"] == "New"


@pytest.mark.asyncio
async def test_update_heuristic_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": "New"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_heuristic_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/heuristics/{fake_id}",
        json={"content": "New"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_heuristic_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(db, module_id, content="H", manager_id=METHODIST_2_ID)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": "New"},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_heuristic_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(db, module_id)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}",
        json={"content": 123},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# PATCH /heuristics/{id}/approve
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_heuristic_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(db, module_id, content="H", is_approved=False)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}/approve",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] is True


@pytest.mark.asyncio
async def test_approve_heuristic_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(db, module_id, content="H", is_approved=False)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}/approve",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_approved"] is True


@pytest.mark.asyncio
async def test_approve_heuristic_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="H", is_approved=False, manager_id=METHODIST_2_ID
    )
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}/approve",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_heuristic_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.patch(f"/api/v1/heuristics/{h_id}/approve")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_approve_heuristic_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/heuristics/{fake_id}/approve",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_heuristic_forbidden_role(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(db, module_id)
    response = await client.patch(
        f"/api/v1/heuristics/{h_id}/approve",
        headers=seminarist_headers,
    )
    assert response.status_code == 403


# ------------------------------------------------------------------
# DELETE /heuristics/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_heuristic_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(db, module_id)
    response = await client.delete(
        f"/api/v1/heuristics/{h_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    get_resp = await client.get(
        f"/api/v1/heuristics/{h_id}",
        headers=admin_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_heuristic_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(db, module_id)
    response = await client.delete(
        f"/api/v1/heuristics/{h_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_heuristic_author_unapproved(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="H", author_id=SEMINARIST_ID, is_approved=False
    )
    response = await client.delete(
        f"/api/v1/heuristics/{h_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_heuristic_author_approved(client, seminarist_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="H", author_id=SEMINARIST_ID, is_approved=True
    )
    response = await client.delete(
        f"/api/v1/heuristics/{h_id}",
        headers=seminarist_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_heuristic_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(db, module_id, manager_id=METHODIST_2_ID)
    response = await client.delete(
        f"/api/v1/heuristics/{h_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_heuristic_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.delete(f"/api/v1/heuristics/{h_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_heuristic_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/heuristics/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


# ------------------------------------------------------------------
# POST /heuristics/{id}/approve-edit
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_edit_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(
        db, module_id, content="Old", pending_content="New", is_approved=True
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/approve-edit",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "New"
    assert data["pending_content"] is None


@pytest.mark.asyncio
async def test_approve_edit_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="Old", pending_content="New", is_approved=True
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/approve-edit",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "New"
    assert data["pending_content"] is None


@pytest.mark.asyncio
async def test_approve_edit_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(
        db,
        module_id,
        content="Old",
        pending_content="New",
        is_approved=True,
        manager_id=METHODIST_2_ID,
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/approve-edit",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_edit_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.post(f"/api/v1/heuristics/{h_id}/approve-edit")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_approve_edit_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.post(
        f"/api/v1/heuristics/{fake_id}/approve-edit",
        headers=admin_headers,
    )
    assert response.status_code == 404


# ------------------------------------------------------------------
# POST /heuristics/{id}/reject-edit
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_edit_admin(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    h_id = await create_heuristic(
        db, module_id, content="Old", pending_content="New", is_approved=True
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/reject-edit",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Old"
    assert data["pending_content"] is None


@pytest.mark.asyncio
async def test_reject_edit_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID
    )
    h_id = await create_heuristic(
        db, module_id, content="Old", pending_content="New", is_approved=True
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/reject-edit",
        headers=methodist1_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Old"
    assert data["pending_content"] is None


@pytest.mark.asyncio
async def test_reject_edit_methodist_other_forbidden(client, methodist1_headers, db):
    module_id = await create_module(
        db, status="published", author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID
    )
    h_id = await create_heuristic(
        db,
        module_id,
        content="Old",
        pending_content="New",
        is_approved=True,
        manager_id=METHODIST_2_ID,
    )
    response = await client.post(
        f"/api/v1/heuristics/{h_id}/reject-edit",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reject_edit_unauthorized(client, db):
    module_id = await create_module(db)
    h_id = await create_heuristic(db, module_id)
    response = await client.post(f"/api/v1/heuristics/{h_id}/reject-edit")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reject_edit_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.post(
        f"/api/v1/heuristics/{fake_id}/reject-edit",
        headers=admin_headers,
    )
    assert response.status_code == 404
