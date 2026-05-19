from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+asyncpg://kms:kms@localhost:5432/kms_auth"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "super-secret-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    class Config:
        """Pydantic config."""

        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
