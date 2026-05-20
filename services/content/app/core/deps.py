"""FastAPI dependencies for authentication and authorization."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis_pool
from app.core.security import decode_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis_pool),
) -> dict:
    """Validate token and return the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        if is_blacklisted:
            raise credentials_exception

    user_id = payload.get("sub")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    manager_id = payload.get("manager_id")

    return {
        "id": user_id,
        "role": role,
        "manager_id": UUID(manager_id) if manager_id else None,
    }


def require_role(allowed_roles: Sequence[str]):
    """FastAPI dependency factory that allows only specified roles."""

    async def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker
