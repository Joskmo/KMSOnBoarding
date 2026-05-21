"""Main FastAPI application for assessment service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.redis import close_redis_pool


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan handler."""
    yield
    await close_redis_pool()


app = FastAPI(
    title="KMS Assessment Service",
    description="Assessment management service for KMS",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return health check status."""
    return {"status": "ok"}
