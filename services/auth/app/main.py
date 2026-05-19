from fastapi import FastAPI

from app.api.v1.routers import auth, roles, users

app = FastAPI(
    title="KMS Auth Service",
    description="Authentication and authorization service for KMS",
    version="0.1.0",
)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return health check status."""
    return {"status": "ok"}
