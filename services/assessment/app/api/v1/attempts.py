"""API endpoints for attempts."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.crud import attempt as attempt_crud, test as test_crud
from app.db.models import Attempt, Test
from app.db.session import get_db
from app.schemas import (
    AttemptCreate,
    AttemptResponse,
    AttemptStartResponse,
    PaginatedAttempts,
)

router = APIRouter(prefix="/attempts", tags=["attempts"])

ATTEMPT_TIMEOUT_MINUTES = 120


def _can_access_test(current_user: dict, test: Test) -> bool:
    """Check if current user can access a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(test.author_id) == str(current_user["id"])
    if role in ("seminarist", "candidate"):
        return test.is_active and str(test.manager_id) == str(current_user["manager_id"])
    return False


def _can_modify_test(current_user: dict, test: Test) -> bool:
    """Check if current user can modify a test."""
    role = current_user["role"]
    if role == "admin":
        return True
    if role == "methodist":
        return str(test.author_id) == str(current_user["id"])
    return False


async def _get_or_fail_active_attempt(
    db: AsyncSession, user_id: UUID, test_id: UUID
) -> Attempt | None:
    """Get active attempt or fail it if timed out."""
    attempt = await attempt_crud.get_active_by_user_and_test(db, user_id, test_id)
    if not attempt:
        return None

    now = datetime.now(UTC)
    started = attempt.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)

    if now - started > timedelta(minutes=ATTEMPT_TIMEOUT_MINUTES):
        # Fail the timed-out attempt
        await attempt_crud.update(
            db,
            db_obj=attempt,
            obj_in={
                "score": 0,
                "is_passed": False,
                "finished_at": now,
            },
        )
        return None

    return attempt


@router.get("/start/{test_id}", response_model=AttemptStartResponse)
async def start_attempt(
    test_id: UUID,
    current_user: dict = Depends(require_role(["seminarist", "candidate"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start or continue a test attempt."""
    test = await test_crud.get_with_questions(db, test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found",
        )

    if not _can_access_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user_id = UUID(current_user["id"])

    # Check for existing active attempt (and fail if timed out)
    existing = await _get_or_fail_active_attempt(db, user_id, test_id)
    if existing:
        questions = test.questions
        return {
            "test_id": test.id,
            "title": test.title,
            "pass_score": test.pass_score,
            "questions": [
                {
                    "id": q.id,
                    "order_index": q.order_index,
                    "text": q.text,
                    "qtype": q.qtype,
                    "options": [{"id": opt["id"], "text": opt["text"]} for opt in q.options],
                }
                for q in questions
            ],
        }

    # Create new attempt
    await attempt_crud.create(
        db,
        obj_in={
            "test_id": test_id,
            "user_id": user_id,
            "manager_id": current_user["manager_id"],
            "answers": {},
            "score": 0,
            "is_passed": False,
        },
    )

    questions = test.questions
    return {
        "test_id": test.id,
        "title": test.title,
        "pass_score": test.pass_score,
        "questions": [
            {
                "id": q.id,
                "order_index": q.order_index,
                "text": q.text,
                "qtype": q.qtype,
                "options": [{"id": opt["id"], "text": opt["text"]} for opt in q.options],
            }
            for q in questions
        ],
    }


@router.post("", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_attempt(
    attempt_in: AttemptCreate,
    current_user: dict = Depends(require_role(["seminarist", "candidate"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit answers and complete an attempt."""
    test = await test_crud.get_with_questions(db, attempt_in.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found",
        )

    if not _can_access_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user_id = UUID(current_user["id"])

    # Find active attempt
    attempt = await _get_or_fail_active_attempt(db, user_id, attempt_in.test_id)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active attempt found for this test",
        )

    # Validate all questions are answered
    question_ids = {str(q.id) for q in test.questions}
    answer_ids = set(attempt_in.answers.keys())

    if answer_ids != question_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Answers must cover all questions in the test",
        )

    # Validate all question_ids in answers exist in test
    unknown = answer_ids - question_ids
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown question ids in answers: {unknown}",
        )

    # Calculate score
    correct_count = 0
    for q in test.questions:
        qid = str(q.id)
        user_answers = set(attempt_in.answers.get(qid, []))
        correct_options = {opt["id"] for opt in q.options if opt["is_correct"]}

        if (q.qtype == "single" and len(user_answers) == 1 and user_answers == correct_options) or (
            q.qtype == "multiple" and user_answers == correct_options
        ):
            correct_count += 1

    total_questions = len(test.questions)
    score = round(correct_count / total_questions * 100) if total_questions > 0 else 0

    is_passed = score >= test.pass_score

    updated = await attempt_crud.update(
        db,
        db_obj=attempt,
        obj_in={
            "answers": attempt_in.answers,
            "score": score,
            "is_passed": is_passed,
            "finished_at": datetime.now(UTC),
        },
    )

    return updated


@router.get("/my", response_model=PaginatedAttempts)
async def list_my_attempts(
    test_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List current user's attempts."""
    user_id = UUID(current_user["id"])

    skip = (page - 1) * size
    attempts, total = await attempt_crud.get_multi(
        db,
        skip=skip,
        limit=size,
        user_id=user_id,
        test_id=test_id,
    )

    return {
        "items": attempts,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/test/{test_id}", response_model=PaginatedAttempts)
async def list_test_attempts(
    test_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role(["admin", "methodist"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all attempts for a test."""
    test = await test_crud.get(db, test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found",
        )

    if not _can_modify_test(current_user, test):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    skip = (page - 1) * size
    attempts, total = await attempt_crud.get_multi(
        db,
        skip=skip,
        limit=size,
        test_id=test_id,
    )

    return {
        "items": attempts,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific attempt by ID."""
    attempt = await attempt_crud.get(db, attempt_id)
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found",
        )

    role = current_user["role"]
    user_id = str(current_user["id"])
    is_owner = str(attempt.user_id) == user_id

    if role == "admin":
        can_view = True
    elif role == "methodist":
        test = await test_crud.get(db, attempt.test_id)
        can_view = is_owner or (test and str(test.author_id) == user_id)
    else:
        can_view = is_owner

    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return attempt
