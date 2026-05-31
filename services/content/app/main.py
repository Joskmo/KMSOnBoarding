"""Main FastAPI application for content service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan handler."""
    yield


app = FastAPI(
    title="KMS Content Service",
    description="Content management service for KMS",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return health check status."""
    return {"status": "ok"}
