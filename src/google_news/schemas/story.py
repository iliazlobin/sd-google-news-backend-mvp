"""Story response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class StoryDetailResponse(BaseModel):
    """GET /v1/stories/{story_id} response."""

    story_id: uuid.UUID
    canonical_headline: str
    article_count: int
    top_sources: list[str]
    category: str
    first_published_at: datetime
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class StoryArticleItem(BaseModel):
    """A single article within a story listing."""

    article_id: uuid.UUID
    headline: str
    publisher_domain: str
    source_authority: float
    published_at: datetime
    url: str

    model_config = {"from_attributes": True}


class StoryArticlesResponse(BaseModel):
    """GET /v1/stories/{story_id}/articles response."""

    story_id: uuid.UUID
    articles: list[StoryArticleItem]
    total: int
    limit: int
    offset: int
