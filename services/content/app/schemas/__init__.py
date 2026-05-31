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
]
