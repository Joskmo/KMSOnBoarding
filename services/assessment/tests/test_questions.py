"""Tests for /api/v1/questions endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_question, create_test

# ------------------------------------------------------------------
# POST /api/v1/tests/{test_id}/questions
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_question_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can create a question in their test."""
    test_id = await create_test(db, title="Test with Questions")

    response = await client.post(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={
            "text": "What is overfitting?",
            "qtype": "single",
            "options": [
                {"id": "a", "text": "Good generalization", "is_correct": False},
                {"id": "b", "text": "Memorizing training data", "is_correct": True},
                {"id": "c", "text": "Not enough data", "is_correct": False},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "What is overfitting?"
    assert data["qtype"] == "single"
    assert len(data["options"]) == 3


@pytest.mark.anyio
async def test_create_question_unauthorized(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Creating question without token returns 401."""
    test_id = await create_test(db)

    response = await client.post(
        f"/api/v1/tests/{test_id}/questions",
        json={"text": "Q?", "options": [{"id": "a", "text": "A", "is_correct": True}]},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_question_forbidden(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Seminarist cannot create a question."""
    test_id = await create_test(db)

    response = await client.post(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "text": "Q?",
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": False},
            ],
        },
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_question_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Creating question for non-existent test returns 404."""
    response = await client.post(
        f"/api/v1/tests/{uuid4()}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={
            "text": "Q?",
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": False},
            ],
        },
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_question_invalid_body(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Invalid question body returns 422."""
    test_id = await create_test(db)

    response = await client.post(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={
            "text": "Q?",
            "qtype": "single",
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": True},  # two correct for single
            ],
        },
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /api/v1/tests/{test_id}/questions
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_questions_methodist(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist sees all questions with is_correct."""
    test_id = await create_test(db)
    await create_question(db, test_id, text="Q1")
    await create_question(db, test_id, text="Q2")

    response = await client.get(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "is_correct" in data[0]["options"][0]


@pytest.mark.anyio
async def test_list_questions_seminarist_no_correct(
    client: AsyncClient,
    seminarist_token: str,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Seminarist sees questions without is_correct."""
    test_id = await create_test(db, is_active=True)
    await create_question(db, test_id, text="Q1")

    response = await client.get(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "is_correct" not in data[0]["options"][0]


@pytest.mark.anyio
async def test_list_questions_unauthorized(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Listing questions without token returns 401."""
    test_id = await create_test(db)

    response = await client.get(f"/api/v1/tests/{test_id}/questions")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_questions_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Listing questions for non-existent test returns 404."""
    response = await client.get(
        f"/api/v1/tests/{uuid4()}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 404


# ------------------------------------------------------------------
# PATCH /api/v1/questions/{question_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_update_question_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can update their question."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id, text="Old Text")

    response = await client.patch(
        f"/api/v1/questions/{question_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"text": "New Text"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "New Text"


@pytest.mark.anyio
async def test_update_question_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Updating non-existent question returns 404."""
    response = await client.patch(
        f"/api/v1/questions/{uuid4()}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"text": "New Text"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_question_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot update another methodist's question."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id)

    response = await client.patch(
        f"/api/v1/questions/{question_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
        json={"text": "New Text"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_question_unauthorized(client: AsyncClient) -> None:
    """Updating question without token returns 401."""
    response = await client.patch(
        f"/api/v1/questions/{uuid4()}",
        json={"text": "New Text"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_question_invalid_body(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Invalid body returns 422."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id)

    response = await client.patch(
        f"/api/v1/questions/{question_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={
            "options": [
                {"id": "a", "text": "A", "is_correct": True},
                {"id": "b", "text": "B", "is_correct": True},
            ],
        },
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# PATCH /api/v1/questions/{question_id}/reorder
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_reorder_question_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can reorder questions."""
    test_id = await create_test(db)
    q1 = await create_question(db, test_id, order_index=0)
    await create_question(db, test_id, order_index=1)
    await create_question(db, test_id, order_index=2)

    # Move q1 to position 2
    response = await client.patch(
        f"/api/v1/questions/{q1}/reorder",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"order_index": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order_index"] == 2

    # Verify order changed
    response = await client.get(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 200
    questions = response.json()
    ids = [q["id"] for q in questions]
    assert ids.index(str(q1)) == 2


@pytest.mark.anyio
async def test_reorder_question_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Reordering non-existent question returns 404."""
    response = await client.patch(
        f"/api/v1/questions/{uuid4()}/reorder",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"order_index": 1},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_reorder_question_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot reorder another methodist's questions."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id)

    response = await client.patch(
        f"/api/v1/questions/{question_id}/reorder",
        headers={"Authorization": f"Bearer {methodist2_token}"},
        json={"order_index": 1},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_reorder_question_unauthorized(client: AsyncClient) -> None:
    """Reordering without token returns 401."""
    response = await client.patch(
        f"/api/v1/questions/{uuid4()}/reorder",
        json={"order_index": 1},
    )
    assert response.status_code == 401


# ------------------------------------------------------------------
# DELETE /api/v1/questions/{question_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_question_success(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can delete their question."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id)

    response = await client.delete(
        f"/api/v1/questions/{question_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(
        f"/api/v1/tests/{test_id}/questions",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    data = response.json()
    assert len(data) == 0


@pytest.mark.anyio
async def test_delete_question_not_found(
    client: AsyncClient,
    methodist1_token: str,
) -> None:
    """Deleting non-existent question returns 404."""
    response = await client.delete(
        f"/api/v1/questions/{uuid4()}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_question_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot delete another methodist's question."""
    test_id = await create_test(db)
    question_id = await create_question(db, test_id)

    response = await client.delete(
        f"/api/v1/questions/{question_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_delete_question_unauthorized(client: AsyncClient) -> None:
    """Deleting question without token returns 401."""
    response = await client.delete(f"/api/v1/questions/{uuid4()}")
    assert response.status_code == 401
