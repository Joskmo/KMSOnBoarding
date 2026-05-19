from fastapi import FastAPI

from app.api.v1.routers import auth, roles, users
from app.db.models import Base
from app.db.session import engine

app = FastAPI(
    title="KMS Auth Service",
    description="Authentication and authorization service for KMS",
    version="0.1.0",
)


@app.on_event("startup")
async def startup() -> None:
    """Create database tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return health check status."""
    return {"status": "ok"}
