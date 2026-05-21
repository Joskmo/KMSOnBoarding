"""Pydantic schemas for lessons."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LessonBase(BaseModel):
    """Base lesson schema."""

    title: str
    r7_uri: str


class LessonCreate(LessonBase):
    """Schema for creating a lesson."""

    order_index: int | None = None


class LessonUpdate(BaseModel):
    """Schema for updating a lesson."""

    title: str | None = None
    r7_uri: str | None = None


class LessonReorder(BaseModel):
    """Schema for reordering a lesson."""

    order_index: int


class LessonResponse(LessonBase):
    """Schema for lesson response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    order_index: int
    author_id: UUID
    created_at: datetime
    updated_at: datetime
