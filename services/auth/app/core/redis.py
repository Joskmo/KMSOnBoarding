"""Redis connection pool singleton."""

import asyncio
from contextlib import suppress

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()
_redis_pool: Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


async def get_redis_pool() -> Redis:
    """Return the singleton Redis connection pool."""
    global _redis_pool, _redis_loop
    current_loop = asyncio.get_running_loop()
    if _redis_pool is None or _redis_loop != current_loop:
        if _redis_pool is not None:
            with suppress(RuntimeError):
                await _redis_pool.aclose()
        _redis_pool = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_loop = current_loop
    return _redis_pool


async def close_redis_pool() -> None:
    """Close the Redis connection pool."""
    global _redis_pool, _redis_loop
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        _redis_loop = None
