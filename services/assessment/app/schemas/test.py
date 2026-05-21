"""Pydantic schemas for tests."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


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

    @computed_field
    @property
    def question_count(self) -> int:
        """Return the number of questions in this test."""
        return len(self.questions) if hasattr(self, "questions") else 0


class PaginatedTests(BaseModel):
    """Schema for paginated test list."""

    items: list[TestResponse]
    total: int
    page: int
    size: int
