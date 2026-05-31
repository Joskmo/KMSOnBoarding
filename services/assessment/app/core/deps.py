"""FastAPI dependencies for authentication and authorization."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status


async def get_current_user(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_manager_id: str | None = Header(None, alias="X-Manager-ID"),
) -> dict:
    """Read authenticated user from gateway headers."""
    if not x_user_id or not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing auth headers",
        )
    return {
        "id": x_user_id,
        "role": x_user_role,
        "manager_id": UUID(x_manager_id) if x_manager_id else None,
    }


def require_role(allowed_roles: Sequence[str]):
    """FastAPI dependency factory that allows only specified roles."""

    async def checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker
