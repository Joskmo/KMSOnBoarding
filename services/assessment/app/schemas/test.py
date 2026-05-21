"""Pydantic schemas for tests."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TestBase(BaseModel):
    """Base test schema."""

    title: str
    description: str | None = None


class TestCreate(TestBase):
    """Schema for creating a test."""

    module_id: UUID
    pass_score: int = 70


class TestUpdate(BaseModel):
    """Schema for updating a test."""

    title: str | None = None
    description: str | None = None
    pass_score: int | None = None
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
    question_count: int = 0
    created_at: datetime
    updated_at: datetime


class PaginatedTests(BaseModel):
    """Schema for paginated test list."""

    items: list[TestResponse]
    total: int
    page: int
    size: int
