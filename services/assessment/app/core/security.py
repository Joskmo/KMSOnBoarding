"""JWT token decoding utilities."""

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def decode_token(token: str) -> dict | None:
    """Decode a JWT access token and return its payload."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
