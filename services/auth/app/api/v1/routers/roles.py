from fastapi import APIRouter, Depends

from app.api.v1.routers.auth import get_current_user
from app.core.enums import UserRole
from app.db.models import User

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
async def list_roles(
    _current_user: User = Depends(get_current_user),
) -> list[dict[str, str]]:
    """List all available roles."""
    return [{"name": role, "description": _role_description(role)} for role in UserRole]


def _role_description(role: str) -> str:
    """Return human-readable description for a role."""
    descriptions = {
        UserRole.ADMIN: "Administrator with full access",
        UserRole.METHODIST: "Content creator and manager",
        UserRole.SEMINARIST: "Seminar conductor",
        UserRole.CANDIDATE: "Learner and test taker",
    }
    return descriptions.get(role, "")
