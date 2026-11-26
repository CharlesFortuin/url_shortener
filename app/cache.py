import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings

redis_client: redis.Redis = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_cached_url(short_code: str) -> str | None:
    try:
        return await redis_client.get(f"url:{short_code}")
    except RedisError:
        return None


async def set_cached_url(
    short_code: str,
    original_url: str,
    ttl_seconds: int | None = None,
) -> None:
    ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
    if ttl <= 0:
        return
    try:
        await redis_client.setex(f"url:{short_code}", ttl, original_url)
    except RedisError:
        pass