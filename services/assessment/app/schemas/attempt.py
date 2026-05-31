"""Pydantic schemas for attempts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import inspect as sa_inspect

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
    test_title: str = ""
    module_id: UUID | None = None
    user_id: UUID
    manager_id: UUID
    answers: dict[str, list[str]]
    score: int
    is_passed: bool
    started_at: datetime
    finished_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _extract_test_info(cls, data: Any) -> Any:
        """Extract test title and module_id from eagerly loaded test."""
        if hasattr(data, "__mapper__"):
            ins = sa_inspect(data)
            if "test" not in ins.unloaded:
                test = getattr(data, "test", None)
                if test is not None:
                    data.test_title = test.title
                    data.module_id = test.module_id
        return data


class AttemptListItem(BaseModel):
    """Schema for attempt list item without answers."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_id: UUID
    test_title: str = ""
    module_id: UUID | None = None
    user_id: UUID
    manager_id: UUID
    score: int
    is_passed: bool
    started_at: datetime
    finished_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _extract_test_info(cls, data: Any) -> Any:
        """Extract test title and module_id from eagerly loaded test."""
        if hasattr(data, "__mapper__"):
            # SQLAlchemy instance — check unloaded first to avoid lazy load
            ins = sa_inspect(data)
            if "test" not in ins.unloaded:
                test = getattr(data, "test", None)
                if test is not None:
                    data.test_title = test.title
                    data.module_id = test.module_id
        return data


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
