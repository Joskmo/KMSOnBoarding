"""Tests for /api/v1/attempts endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import SEMINARIST_ID, create_question, create_test

# ------------------------------------------------------------------
# GET /api/v1/attempts/start/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_start_attempt_success(
    client: AsyncClient,
    seminarist_token: str,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Seminarist can start an attempt."""
    test_id = await create_test(db, title="Attempt Test", is_active=True)
    await create_question(db, test_id, text="Q1")
    await create_question(db, test_id, text="Q2")

    response = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Attempt Test"
    assert len(data["questions"]) == 2
    # is_correct must not be present
    assert "is_correct" not in data["questions"][0]["options"][0]


@pytest.mark.anyio
async def test_start_attempt_unauthorized(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Starting attempt without token returns 401."""
    test_id = await create_test(db)

    response = await client.get(f"/api/v1/attempts/start/{test_id}")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_start_attempt_forbidden(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot start an attempt."""
    test_id = await create_test(db, is_active=True)

    response = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_start_attempt_not_found(
    client: AsyncClient,
    seminarist_token: str,
) -> None:
    """Starting attempt for non-existent test returns 404."""
    response = await client.get(
        f"/api/v1/attempts/start/{uuid4()}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_start_attempt_candidate(
    client: AsyncClient,
    candidate_token: str,
    db: AsyncSession,
) -> None:
    """Candidate can start an attempt."""
    test_id = await create_test(db, title="Candidate Test", is_active=True)
    await create_question(db, test_id)

    response = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_start_inactive_test_forbidden(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Starting inactive test returns 403."""
    test_id = await create_test(db, is_active=False)

    response = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_continue_existing_attempt(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Repeated start returns existing active attempt without creating new one."""
    test_id = await create_test(db, title="Continue", is_active=True)
    await create_question(db, test_id)

    resp1 = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert resp1.status_code == 200

    resp2 = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert resp2.status_code == 200

    # Should still be only 1 active attempt in DB
    response = await client.get(
        "/api/v1/attempts/my",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    data = response.json()
    active = [a for a in data["items"] if a["score"] == 0 and not a["is_passed"]]
    assert len(active) == 1


# ------------------------------------------------------------------
# POST /api/v1/attempts
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_submit_attempt_success_single(
    client: AsyncClient,
    seminarist_token: str,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Seminarist submits answers for single-choice questions."""
    test_id = await create_test(db, title="Single Test", is_active=True, pass_score=50)
    q1 = await create_question(
        db,
        test_id,
        text="Q1",
        qtype="single",
        options=[
            {"id": "a", "text": "Wrong", "is_correct": False},
            {"id": "b", "text": "Correct", "is_correct": True},
        ],
    )
    q2 = await create_question(
        db,
        test_id,
        text="Q2",
        qtype="single",
        options=[
            {"id": "a", "text": "Wrong", "is_correct": False},
            {"id": "b", "text": "Correct", "is_correct": True},
        ],
    )

    # Start attempt
    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    # Submit all correct
    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["b"],
                str(q2): ["b"],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 100
    assert data["is_passed"] is True


@pytest.mark.anyio
async def test_submit_attempt_score_boundary(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """is_passed is True when score == pass_score."""
    test_id = await create_test(db, title="Boundary", is_active=True, pass_score=50)
    q1 = await create_question(
        db,
        test_id,
        text="Q1",
        qtype="single",
        options=[
            {"id": "a", "text": "Wrong", "is_correct": False},
            {"id": "b", "text": "Correct", "is_correct": True},
        ],
    )
    q2 = await create_question(
        db,
        test_id,
        text="Q2",
        qtype="single",
        options=[
            {"id": "a", "text": "Wrong", "is_correct": False},
            {"id": "b", "text": "Correct", "is_correct": True},
        ],
    )

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    # 1 correct out of 2 = 50%
    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["b"],
                str(q2): ["a"],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 50
    assert data["is_passed"] is True


@pytest.mark.anyio
async def test_submit_attempt_multiple(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Multiple choice requires exact match."""
    test_id = await create_test(db, title="Multi", is_active=True)
    q1 = await create_question(
        db,
        test_id,
        text="Q1",
        qtype="multiple",
        options=[
            {"id": "a", "text": "A", "is_correct": True},
            {"id": "b", "text": "B", "is_correct": True},
            {"id": "c", "text": "C", "is_correct": False},
        ],
    )

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    # Exact match
    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["a", "b"],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 100


@pytest.mark.anyio
async def test_submit_attempt_multiple_partial(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Partial match on multiple choice gives 0 points."""
    test_id = await create_test(db, title="Multi Partial", is_active=True)
    q1 = await create_question(
        db,
        test_id,
        text="Q1",
        qtype="multiple",
        options=[
            {"id": "a", "text": "A", "is_correct": True},
            {"id": "b", "text": "B", "is_correct": True},
            {"id": "c", "text": "C", "is_correct": False},
        ],
    )

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    # Only one correct selected
    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["a"],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 0
    assert data["is_passed"] is False


@pytest.mark.anyio
async def test_submit_attempt_unknown_question(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Unknown question_id in answers returns 422."""
    test_id = await create_test(db, title="Unknown", is_active=True)
    q1 = await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["a"],
                str(uuid4()): ["b"],
            },
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_attempt_missing_answers(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Missing answers for some questions returns 422."""
    test_id = await create_test(db, title="Missing", is_active=True)
    q1 = await create_question(db, test_id)
    await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={
            "test_id": str(test_id),
            "answers": {
                str(q1): ["a"],
                # missing q2
            },
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_attempt_unauthorized(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Submitting attempt without token returns 401."""
    test_id = await create_test(db)

    response = await client.post(
        "/api/v1/attempts",
        json={"test_id": str(test_id), "answers": {}},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_submit_attempt_forbidden(
    client: AsyncClient,
    methodist1_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot submit an attempt."""
    test_id = await create_test(db, is_active=True)

    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {methodist1_token}"},
        json={"test_id": str(test_id), "answers": {}},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_submit_attempt_not_found(
    client: AsyncClient,
    seminarist_token: str,
) -> None:
    """Submitting attempt for non-existent test returns 404."""
    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(uuid4()), "answers": {}},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_submit_without_start(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Submitting without starting returns 404."""
    test_id = await create_test(db, is_active=True)
    q1 = await create_question(db, test_id)

    response = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(test_id), "answers": {str(q1): ["a"]}},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_timeout_auto_fail(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Timed-out attempt is auto-failed and new one can be started."""
    from datetime import UTC, datetime, timedelta

    test_id = await create_test(db, title="Timeout", is_active=True)
    await create_question(db, test_id)

    # Start attempt
    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )

    # Manually set started_at to 3 hours ago (simulate timeout)
    from app.crud import attempt as attempt_crud

    attempts, _ = await attempt_crud.get_multi(db, user_id=SEMINARIST_ID)
    active = [a for a in attempts if a.test_id == test_id and a.score == 0 and not a.is_passed]
    assert len(active) == 1
    active[0].started_at = datetime.now(UTC) - timedelta(hours=3)
    await db.commit()

    # Next start should fail old attempt and allow new start
    response = await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200


# ------------------------------------------------------------------
# GET /api/v1/attempts/my
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_my_attempts(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """User can list their own attempts."""
    test_id = await create_test(db, is_active=True)
    q1 = await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    post_resp = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(test_id), "answers": {str(q1): ["a"]}},
    )
    assert post_resp.status_code == 201

    response = await client.get(
        "/api/v1/attempts/my",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "answers" not in data["items"][0]


@pytest.mark.anyio
async def test_list_my_attempts_unauthorized(client: AsyncClient) -> None:
    """Listing attempts without token returns 401."""
    response = await client.get("/api/v1/attempts/my")
    assert response.status_code == 401


# ------------------------------------------------------------------
# GET /api/v1/attempts/test/{test_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_test_attempts(
    client: AsyncClient,
    methodist1_token: str,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """Methodist can list attempts for their test."""
    test_id = await create_test(db, is_active=True)
    q1 = await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    post_resp = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(test_id), "answers": {str(q1): ["a"]}},
    )
    assert post_resp.status_code == 201

    response = await client.get(
        f"/api/v1/attempts/test/{test_id}",
        headers={"Authorization": f"Bearer {methodist1_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.anyio
async def test_list_test_attempts_forbidden(
    client: AsyncClient,
    methodist2_token: str,
    db: AsyncSession,
) -> None:
    """Methodist cannot list attempts for another's test."""
    test_id = await create_test(db)

    response = await client.get(
        f"/api/v1/attempts/test/{test_id}",
        headers={"Authorization": f"Bearer {methodist2_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_list_test_attempts_unauthorized(client: AsyncClient) -> None:
    """Listing test attempts without token returns 401."""
    response = await client.get(f"/api/v1/attempts/test/{uuid4()}")
    assert response.status_code == 401


# ------------------------------------------------------------------
# GET /api/v1/attempts/{attempt_id}
# ------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_attempt(
    client: AsyncClient,
    seminarist_token: str,
    db: AsyncSession,
) -> None:
    """User can get their own attempt."""
    test_id = await create_test(db, is_active=True)
    q1 = await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    post_resp = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(test_id), "answers": {str(q1): ["a"]}},
    )
    attempt_id = post_resp.json()["id"]

    response = await client.get(
        f"/api/v1/attempts/{attempt_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == attempt_id
    assert "answers" in data


@pytest.mark.anyio
async def test_get_attempt_not_found(
    client: AsyncClient,
    seminarist_token: str,
) -> None:
    """Getting non-existent attempt returns 404."""
    response = await client.get(
        f"/api/v1/attempts/{uuid4()}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_attempt_forbidden(
    client: AsyncClient,
    seminarist_token: str,
    candidate_token: str,
    db: AsyncSession,
) -> None:
    """Candidate cannot get seminarist's attempt."""
    test_id = await create_test(db, is_active=True)
    q1 = await create_question(db, test_id)

    await client.get(
        f"/api/v1/attempts/start/{test_id}",
        headers={"Authorization": f"Bearer {seminarist_token}"},
    )
    post_resp = await client.post(
        "/api/v1/attempts",
        headers={"Authorization": f"Bearer {seminarist_token}"},
        json={"test_id": str(test_id), "answers": {str(q1): ["a"]}},
    )
    attempt_id = post_resp.json()["id"]

    response = await client.get(
        f"/api/v1/attempts/{attempt_id}",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_attempt_unauthorized(client: AsyncClient) -> None:
    """Getting attempt without token returns 401."""
    response = await client.get(f"/api/v1/attempts/{uuid4()}")
    assert response.status_code == 401
