from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import URLCreateRequest, URLCreateResponse, URLStatsResponse
from app.services.url_service import create_short_url, get_url_stats, resolve_short_url

router = APIRouter()


@router.post(
    "/api/v1/urls",
    response_model=URLCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def shorten_url(
    payload: URLCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> URLCreateResponse:
    url_entry = await create_short_url(
        db=db,
        original_url=str(payload.original_url),
        expires_at=payload.expires_at,
    )
    return URLCreateResponse(
        short_code=url_entry.short_code,  # type: ignore[arg-type]
        short_url=f"{settings.base_url.rstrip('/')}/{url_entry.short_code}",
        original_url=url_entry.original_url,
        created_at=url_entry.created_at,
        expires_at=url_entry.expires_at,
    )


@router.get("/api/v1/urls/{short_code}/stats", response_model=URLStatsResponse)
async def url_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> URLStatsResponse:
    url_entry = await get_url_stats(db=db, short_code=short_code)
    if url_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )
    return URLStatsResponse(
        short_code=url_entry.short_code,  # type: ignore[arg-type]
        original_url=url_entry.original_url,
        click_count=url_entry.click_count,
        created_at=url_entry.created_at,
        expires_at=url_entry.expires_at,
    )


@router.get("/{short_code}")
async def redirect_to_original(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    original_url = await resolve_short_url(db=db, short_code=short_code)
    if original_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found or expired.",
        )
    return RedirectResponse(
        url=original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )