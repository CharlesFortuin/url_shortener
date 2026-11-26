from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cached_url, set_cached_url
from app.config import settings
from app.models import URL
from app.services.base62 import ID_OFFSET, encode


def _compute_ttl(expires_at: datetime | None) -> int:
    if expires_at is None:
        return settings.cache_ttl_seconds
    remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return max(0, min(settings.cache_ttl_seconds, remaining))


async def create_short_url(
    db: AsyncSession,
    original_url: str,
    expires_at: datetime | None = None,
) -> URL:
    url_entry = URL(original_url=original_url, expires_at=expires_at)
    db.add(url_entry)
    await db.flush()

    url_entry.short_code = encode(url_entry.id + ID_OFFSET)
    await db.commit()
    await db.refresh(url_entry)

    ttl = _compute_ttl(url_entry.expires_at)
    await set_cached_url(url_entry.short_code, url_entry.original_url, ttl)
    return url_entry


async def increment_click_count(db: AsyncSession, short_code: str) -> None:
    await db.execute(
        update(URL)
        .where(URL.short_code == short_code)
        .values(click_count=URL.click_count + 1)
    )
    await db.commit()


async def resolve_short_url(db: AsyncSession, short_code: str) -> str | None:
    cached_url = await get_cached_url(short_code)
    if cached_url is not None:
        await increment_click_count(db, short_code)
        return cached_url

    stmt = select(URL).where(URL.short_code == short_code)
    result = await db.execute(stmt)
    url_entry = result.scalar_one_or_none()

    if url_entry is None:
        return None

    if url_entry.expires_at and url_entry.expires_at <= datetime.now(timezone.utc):
        return None

    ttl = _compute_ttl(url_entry.expires_at)
    await set_cached_url(short_code, url_entry.original_url, ttl)
    await increment_click_count(db, short_code)
    return url_entry.original_url


async def get_url_stats(db: AsyncSession, short_code: str) -> URL | None:
    stmt = select(URL).where(URL.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()