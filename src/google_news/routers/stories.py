"""GET /v1/stories/{story_id} + /v1/stories/{story_id}/articles."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.models.article import Article
from google_news.models.story import Story

router = APIRouter(prefix="/v1", tags=["stories"])


@router.get("/stories/{story_id}")
async def get_story_detail(
    story_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return story detail with canonical headline + top sources."""
    story = await db.get(Story, story_id)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": f"Story {story_id} not found"},
        )

    return {
        "story_id": str(story.story_id),
        "canonical_headline": story.canonical_headline,
        "article_count": story.article_count,
        "top_sources": list(story.top_sources) if story.top_sources else [],
        "category": story.category,
        "first_published_at": story.first_published_at.isoformat(),
        "last_updated_at": story.last_updated_at.isoformat(),
    }


@router.get("/stories/{story_id}/articles")
async def get_story_articles(
    story_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated articles within a story, sorted by authority DESC then recency DESC."""
    story = await db.get(Story, story_id)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": f"Story {story_id} not found"},
        )

    # Count total
    count_stmt = select(func.count()).select_from(Article).where(Article.story_id == story_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch articles ordered by authority DESC, then published_at DESC
    stmt = (
        select(Article)
        .where(Article.story_id == story_id)
        .order_by(Article.source_authority.desc(), Article.published_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.scalars().all()

    return {
        "story_id": str(story_id),
        "articles": [
            {
                "article_id": str(a.article_id),
                "headline": a.headline,
                "publisher_domain": a.publisher_domain,
                "source_authority": a.source_authority,
                "published_at": a.published_at.isoformat(),
                "url": a.url,
            }
            for a in articles
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
