"""Feed response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class FeedStory(BaseModel):
    """A story as it appears in the ranked feed."""

    story_id: uuid.UUID
    canonical_headline: str
    snippet: str | None
    source_count: int
    top_sources: list[str]
    category: str
    published_at: datetime
    score: float
    thumbnail_url: str | None


class FeedResponse(BaseModel):
    """GET /v1/feed response."""

    stories: list[FeedStory]
    user_id: uuid.UUID
