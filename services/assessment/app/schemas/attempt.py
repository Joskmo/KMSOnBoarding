"""Pydantic schemas for attempts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.question import QuestionForAttempt


class AttemptCreate(BaseModel):
    """Schema for creating an attempt."""

    test_id: UUID
    answers: dict[str, list[str]]


class AttemptResponse(BaseModel):
    """Schema for attempt response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_id: UUID
    user_id: UUID
    manager_id: UUID
    answers: dict[str, list[str]]
    score: int
    is_passed: bool
    started_at: datetime
    finished_at: datetime


class AttemptListItem(BaseModel):
    """Schema for attempt list item without answers."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_id: UUID
    user_id: UUID
    manager_id: UUID
    score: int
    is_passed: bool
    started_at: datetime
    finished_at: datetime


class PaginatedAttempts(BaseModel):
    """Schema for paginated attempt list."""

    items: list[AttemptListItem]
    total: int
    page: int
    size: int


class AttemptStartResponse(BaseModel):
    """Schema for starting a test attempt."""

    test_id: UUID
    title: str
    pass_score: int
    questions: list[QuestionForAttempt]
