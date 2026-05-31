"""Pydantic schemas for modules."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModuleBase(BaseModel):
    """Base module schema."""

    title: str
    description: str | None = None


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""

    title: str | None = None
    description: str | None = None


class ModuleResponse(ModuleBase):
    """Schema for module response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    author_id: UUID
    manager_id: UUID
    lesson_count: int = 0
    created_at: datetime
    updated_at: datetime


class PaginatedModules(BaseModel):
    """Schema for paginated module list."""

    items: list[ModuleResponse]
    total: int
    page: int
    size: int


class ModuleStatusUpdate(BaseModel):
    """Schema for updating module status."""

    status: Literal["draft", "published", "archived"]


class ModuleAssignmentCreate(BaseModel):
    """Schema for creating module assignments."""

    user_ids: list[UUID]


class ModuleAssignmentResponse(BaseModel):
    """Schema for module assignment response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    user_id: UUID
    assigned_by: UUID
    created_at: datetime
