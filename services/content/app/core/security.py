"""JWT security utilities."""

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token, returning the payload or None."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
