"""Aggregate router for API v1."""

from fastapi import APIRouter

from app.api.v1 import assignments, heuristics, lessons, modules

router = APIRouter(prefix="/api/v1")

router.include_router(modules.router)
router.include_router(lessons.router)
router.include_router(heuristics.router)
router.include_router(assignments.router)
