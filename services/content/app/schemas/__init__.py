"""Content service schemas."""

from app.schemas.heuristic import (
    HeuristicCreate,
    HeuristicResponse,
    HeuristicUpdate,
)
from app.schemas.lesson import (
    LessonCreate,
    LessonReorder,
    LessonResponse,
    LessonUpdate,
    R7UriValidationRequest,
    R7UriValidationResponse,
)
from app.schemas.module import (
    ModuleAssignmentCreate,
    ModuleAssignmentResponse,
    ModuleCreate,
    ModuleResponse,
    ModuleStatusUpdate,
    ModuleUpdate,
    PaginatedModules,
)

__all__ = [
    "HeuristicCreate",
    "HeuristicResponse",
    "HeuristicUpdate",
    "LessonCreate",
    "LessonReorder",
    "LessonResponse",
    "LessonUpdate",
    "ModuleAssignmentCreate",
    "ModuleAssignmentResponse",
    "ModuleCreate",
    "ModuleResponse",
    "ModuleStatusUpdate",
    "ModuleUpdate",
    "PaginatedModules",
    "R7UriValidationRequest",
    "R7UriValidationResponse",
]
