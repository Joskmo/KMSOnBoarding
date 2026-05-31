"""Pydantic schemas for tests."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import inspect as sa_inspect


class TestBase(BaseModel):
    """Base test schema."""

    title: str
    description: str | None = None


class TestCreate(TestBase):
    """Schema for creating a test."""

    module_id: UUID
    pass_score: int = Field(70, ge=0, le=100)


class TestUpdate(BaseModel):
    """Schema for updating a test."""

    title: str | None = None
    description: str | None = None
    module_id: UUID | None = None
    pass_score: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class TestResponse(TestBase):
    """Schema for test response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    pass_score: int
    author_id: UUID
    manager_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    question_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def _compute_question_count(cls, data: Any) -> Any:
        """Set question_count from eagerly loaded questions if available."""
        if hasattr(data, "__mapper__"):
            # SQLAlchemy instance
            ins = sa_inspect(data)
            if "questions" not in ins.unloaded:
                data.question_count = len(data.questions)
            else:
                data.question_count = 0
        return data


class PaginatedTests(BaseModel):
    """Schema for paginated test list."""

    items: list[TestResponse]
    total: int
    page: int
    size: int
