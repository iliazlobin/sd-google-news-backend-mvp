"""POST /v1/articles — ingest a new article, triggering clustering."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.models.article import Article
from google_news.schemas.article import ArticleCreate
from google_news.services.cluster_service import assign_article_to_story

router = APIRouter(prefix="/v1", tags=["articles"])


@router.post("/articles", status_code=status.HTTP_201_CREATED)
async def ingest_article(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a new article. Idempotent on URL — duplicate returns 409."""
    # Check URL uniqueness
    existing = await db.execute(select(Article).where(Article.url == str(body.url)))
    existing_article = existing.scalar_one_or_none()
    if existing_article is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Article with this URL already exists",
                "existing_article_id": str(existing_article.article_id),
                "article_id": str(existing_article.article_id),
                "story_id": str(existing_article.story_id) if existing_article.story_id else None,
                "url": str(body.url),
            },
        )

    # Create article
    article = Article(
        url=str(body.url),
        headline=body.headline,
        publisher_domain=body.publisher_domain,
        published_at=body.published_at,
        snippet=body.snippet,
        language=body.language,
        region=body.region,
        source_authority=body.source_authority,
    )
    db.add(article)
    await db.flush()

    # Trigger clustering
    story_id = await assign_article_to_story(db, article)

    await db.commit()

    return {
        "article_id": str(article.article_id),
        "story_id": str(story_id),
        "url": str(body.url),
    }
