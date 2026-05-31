"""Tests for lesson endpoints."""

from uuid import uuid4

import pytest

from tests.conftest import (
    ADMIN_ID,
    METHODIST_1_ID,
    METHODIST_2_ID,
    create_lesson,
    create_module,
)

# ------------------------------------------------------------------
# POST /modules/{id}/lessons
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_lesson_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson 1", "r7_uri": "https://r7.example.com/1"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Lesson 1"
    assert data["order_index"] == 0
    assert data["module_id"] == str(module_id)


@pytest.mark.asyncio
async def test_create_lesson_auto_order_index(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    await create_lesson(db, module_id, order_index=0)

    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson 2", "r7_uri": "https://r7.example.com/2"},
        headers=methodist1_headers,
    )
    assert response.status_code == 201
    assert response.json()["order_index"] == 1


@pytest.mark.asyncio
async def test_create_lesson_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson 1", "r7_uri": "https://r7.example.com/1"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_lesson_forbidden(client, seminarist_headers, db):
    module_id = await create_module(db)
    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson 1", "r7_uri": "https://r7.example.com/1"},
        headers=seminarist_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_lesson_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.post(
        f"/api/v1/modules/{fake_id}/lessons",
        json={"title": "Lesson 1", "r7_uri": "https://r7.example.com/1"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_lesson_without_r7_uri(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson 1"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Lesson 1"
    assert data["r7_uri"] is None


@pytest.mark.asyncio
async def test_create_lesson_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    response = await client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"r7_uri": "https://r7.example.com/1"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /modules/{id}/lessons
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_lessons_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_lesson(db, module_id, title="L1")
    await create_lesson(db, module_id, title="L2")

    response = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "L1"
    assert data[1]["title"] == "L2"


@pytest.mark.asyncio
async def test_list_lessons_ordered_by_index(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    await create_lesson(db, module_id, title="L3", order_index=2)
    await create_lesson(db, module_id, title="L1", order_index=0)
    await create_lesson(db, module_id, title="L2", order_index=1)

    response = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=admin_headers,
    )
    data = response.json()
    assert [l["title"] for l in data] == ["L1", "L2", "L3"]


@pytest.mark.asyncio
async def test_list_lessons_unauthorized(client, db):
    module_id = await create_module(db)
    response = await client.get(f"/api/v1/modules/{module_id}/lessons")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_lessons_module_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/v1/modules/{fake_id}/lessons",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_lessons_forbidden(client, methodist1_headers, methodist2_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    response = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


# ------------------------------------------------------------------
# GET /lessons/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lesson_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    lesson_id = await create_lesson(db, module_id, title="L1")

    response = await client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "L1"


@pytest.mark.asyncio
async def test_get_lesson_unauthorized(client, db):
    module_id = await create_module(db)
    lesson_id = await create_lesson(db, module_id)
    response = await client.get(f"/api/v1/lessons/{lesson_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_lesson_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.get(
        f"/api/v1/lessons/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_lesson_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


# ------------------------------------------------------------------
# PATCH /lessons/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_lesson_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Updated Lesson"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Lesson"


@pytest.mark.asyncio
async def test_update_lesson_methodist_own(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_1_ID, manager_id=METHODIST_1_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Updated"},
        headers=methodist1_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_lesson_unauthorized(client, db):
    module_id = await create_module(db)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Updated"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_lesson_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/lessons/{fake_id}",
        json={"title": "Updated"},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_lesson_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Updated"},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_lesson_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": 123},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# PATCH /lessons/{id}/reorder
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reorder_lesson_down(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    l1 = await create_lesson(db, module_id, title="L1", order_index=0)
    l2 = await create_lesson(db, module_id, title="L2", order_index=1)
    l3 = await create_lesson(db, module_id, title="L3", order_index=2)

    response = await client.patch(
        f"/api/v1/lessons/{l1}/reorder",
        json={"order_index": 2},
        headers=admin_headers,
    )
    assert response.status_code == 200

    # Verify order
    resp = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=admin_headers,
    )
    data = resp.json()
    assert data[0]["id"] == str(l2)
    assert data[0]["order_index"] == 0
    assert data[1]["id"] == str(l3)
    assert data[1]["order_index"] == 1
    assert data[2]["id"] == str(l1)
    assert data[2]["order_index"] == 2


@pytest.mark.asyncio
async def test_reorder_lesson_up(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    l1 = await create_lesson(db, module_id, title="L1", order_index=0)
    l2 = await create_lesson(db, module_id, title="L2", order_index=1)
    l3 = await create_lesson(db, module_id, title="L3", order_index=2)

    response = await client.patch(
        f"/api/v1/lessons/{l3}/reorder",
        json={"order_index": 0},
        headers=admin_headers,
    )
    assert response.status_code == 200

    resp = await client.get(
        f"/api/v1/modules/{module_id}/lessons",
        headers=admin_headers,
    )
    data = resp.json()
    assert data[0]["id"] == str(l3)
    assert data[0]["order_index"] == 0
    assert data[1]["id"] == str(l1)
    assert data[1]["order_index"] == 1
    assert data[2]["id"] == str(l2)
    assert data[2]["order_index"] == 2


@pytest.mark.asyncio
async def test_reorder_lesson_same_index(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    l1 = await create_lesson(db, module_id, title="L1", order_index=0)

    response = await client.patch(
        f"/api/v1/lessons/{l1}/reorder",
        json={"order_index": 0},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["order_index"] == 0


@pytest.mark.asyncio
async def test_reorder_lesson_unauthorized(client, db):
    module_id = await create_module(db)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}/reorder",
        json={"order_index": 5},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reorder_lesson_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.patch(
        f"/api/v1/lessons/{fake_id}/reorder",
        json={"order_index": 0},
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reorder_lesson_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}/reorder",
        json={"order_index": 0},
        headers=methodist1_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_reorder_lesson_invalid(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.patch(
        f"/api/v1/lessons/{lesson_id}/reorder",
        json={"order_index": "zero"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# DELETE /lessons/{id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_lesson_happy(client, admin_headers, db):
    module_id = await create_module(db, author_id=ADMIN_ID, manager_id=ADMIN_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.delete(
        f"/api/v1/lessons/{lesson_id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    get_resp = await client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=admin_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_lesson_unauthorized(client, db):
    module_id = await create_module(db)
    lesson_id = await create_lesson(db, module_id)
    response = await client.delete(f"/api/v1/lessons/{lesson_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_lesson_not_found(client, admin_headers):
    fake_id = str(uuid4())
    response = await client.delete(
        f"/api/v1/lessons/{fake_id}",
        headers=admin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_lesson_forbidden(client, methodist1_headers, db):
    module_id = await create_module(db, author_id=METHODIST_2_ID, manager_id=METHODIST_2_ID)
    lesson_id = await create_lesson(db, module_id)
    response = await client.delete(
        f"/api/v1/lessons/{lesson_id}",
        headers=methodist1_headers,
    )
    assert response.status_code == 403


# ------------------------------------------------------------------
# POST /lessons/validate-r7-uri
# ------------------------------------------------------------------

from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_validate_r7_uri_success(client, admin_headers):
    with patch("app.api.v1.lessons.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.head = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        response = await client.post(
            "/api/v1/lessons/validate-r7-uri",
            json={"uri": "https://cddisk.r7.ru/doc.html?uid=123"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message"] == "Ссылка доступна"
        assert data["status_code"] == 200


@pytest.mark.asyncio
async def test_validate_r7_uri_forbidden(client, admin_headers):
    with patch("app.api.v1.lessons.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = AsyncMock()
        mock_response.status_code = 403
        mock_client.head = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        response = await client.post(
            "/api/v1/lessons/validate-r7-uri",
            json={"uri": "https://cddisk.r7.ru/doc.html?uid=123"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "требует авторизации" in data["message"]
        assert data["status_code"] == 403


@pytest.mark.asyncio
async def test_validate_r7_uri_not_found(client, admin_headers):
    with patch("app.api.v1.lessons.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.head = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        response = await client.post(
            "/api/v1/lessons/validate-r7-uri",
            json={"uri": "https://cddisk.r7.ru/doc.html?uid=123"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "404" in data["message"]
        assert data["status_code"] == 404


@pytest.mark.asyncio
async def test_validate_r7_uri_timeout(client, admin_headers):
    with patch("app.api.v1.lessons.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        import httpx

        mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_cls.return_value = mock_client

        response = await client.post(
            "/api/v1/lessons/validate-r7-uri",
            json={"uri": "https://cddisk.r7.ru/doc.html?uid=123"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "время ожидания" in data["message"]


@pytest.mark.asyncio
async def test_validate_r7_uri_invalid_format(client, admin_headers):
    response = await client.post(
        "/api/v1/lessons/validate-r7-uri",
        json={"uri": "not-a-url"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Некорректный формат" in data["message"]


@pytest.mark.asyncio
async def test_validate_r7_uri_unauthorized(client):
    response = await client.post(
        "/api/v1/lessons/validate-r7-uri",
        json={"uri": "https://example.com"},
    )
    assert response.status_code == 401
