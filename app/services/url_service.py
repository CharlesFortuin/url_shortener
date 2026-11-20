from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import URL
from app.services.base62 import ID_OFFSET, encode


async def create_short_url(
    db: AsyncSession,
    original_url: str,
    expires_at: datetime | None = None,
) -> URL:
    url_entry = URL(original_url=original_url, expires_at=expires_at)
    db.add(url_entry)
    await db.flush()  # Populates url_entry.id from PostgreSQL without committing yet

    url_entry.short_code = encode(url_entry.id + ID_OFFSET)
    await db.commit()
    await db.refresh(url_entry)
    return url_entry


async def resolve_short_url(db: AsyncSession, short_code: str) -> str | None:
    stmt = select(URL).where(URL.short_code == short_code)
    result = await db.execute(stmt)
    url_entry = result.scalar_one_or_none()

    if url_entry is None:
        return None

    if url_entry.expires_at and url_entry.expires_at <= datetime.now(timezone.utc):
        return None

    await db.execute(
        update(URL)
        .where(URL.id == url_entry.id)
        .values(click_count=URL.click_count + 1)
    )
    await db.commit()
    return url_entry.original_url


async def get_url_stats(db: AsyncSession, short_code: str) -> URL | None:
    stmt = select(URL).where(URL.short_code == short_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()