"""Search response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SearchResult(BaseModel):
    """A single search result item."""

    article_id: uuid.UUID
    story_id: uuid.UUID | None
    headline: str
    snippet: str | None
    publisher_domain: str
    published_at: datetime
    relevance: float


class SearchResponse(BaseModel):
    """GET /v1/search response."""

    results: list[SearchResult]
    query: str
    total: int
