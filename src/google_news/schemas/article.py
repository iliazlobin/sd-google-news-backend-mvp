"""Article request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ArticleCreate(BaseModel):
    """Payload for POST /v1/articles."""

    url: HttpUrl
    headline: str = Field(..., min_length=1, max_length=500)
    publisher_domain: str = Field(..., min_length=1, max_length=255)
    published_at: datetime
    snippet: str | None = Field(None, max_length=200)
    language: str = Field("en", min_length=2, max_length=5)
    region: str = Field("us", min_length=2, max_length=5)
    source_authority: float = Field(0.5, ge=0.0, le=1.0)


class ArticleResponse(BaseModel):
    """Response for a single article."""

    article_id: uuid.UUID
    url: str
    headline: str
    publisher_domain: str
    published_at: datetime
    source_authority: float
    story_id: uuid.UUID | None

    model_config = {"from_attributes": True}
