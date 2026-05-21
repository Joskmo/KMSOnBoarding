"""Aggregate router for API v1."""

from fastapi import APIRouter

from app.api.v1 import tests

router = APIRouter(prefix="/api/v1")

router.include_router(tests.router)
