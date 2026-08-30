from asyncio import Lock
from functools import lru_cache

import redis.asyncio as redis
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate, RedisBucket

from app.config import Settings, get_settings
from app.database import get_redis_client


class RateLimiterService:
    def __init__(
        self, redis_client: redis.Redis | None = None, settings: Settings | None = None
    ) -> None:
        self._redis_client = redis_client or get_redis_client()
        self._settings = settings or get_settings()
        self._limiter: Limiter | None = None
        self._lock = Lock()

    async def _get_limiter(self) -> Limiter:
        if self._limiter is None:
            async with self._lock:
                if self._limiter is None:
                    rates = [Rate(1, Duration.SECOND * self._settings.rate_limit)]
                    bucket = await RedisBucket.init(
                        rates, self._redis_client, self._settings.bucket_key
                    )  # type: ignore
                    self._limiter = Limiter(bucket)
        return self._limiter

    async def get_limiter_dependency(self) -> RateLimiter:
        return RateLimiter(limiter=await self._get_limiter())


@lru_cache
def get_rate_limiter_service() -> RateLimiterService:
    """
    A cached factory function for RateLimiterService object.
    """
    return RateLimiterService()
