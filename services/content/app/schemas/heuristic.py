"""Pydantic schemas for heuristics."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HeuristicBase(BaseModel):
    """Base heuristic schema."""

    content: str


class HeuristicCreate(HeuristicBase):
    """Schema for creating a heuristic."""


class HeuristicUpdate(BaseModel):
    """Schema for updating a heuristic."""

    content: str | None = None


class HeuristicResponse(HeuristicBase):
    """Schema for heuristic response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    author_id: UUID
    manager_id: UUID
    is_approved: bool
    created_at: datetime
    updated_at: datetime
