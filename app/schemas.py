from datetime import datetime

from pydantic import BaseModel, HttpUrl


class URLCreateRequest(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None


class URLCreateResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None


class URLStatsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: datetime | None = None