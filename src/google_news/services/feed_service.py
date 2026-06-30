"""Feed ranking logic: freshness decay, authority multiplier, topic boost."""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.models.article import Article
from google_news.models.story import Story
from google_news.models.user_profile import UserProfile
from google_news.services.redis_client import cache_get, cache_set

# λ tuned for 50% decay at 6 hours
# e^(-λ × 6) = 0.5  →  λ = ln(2) / 6
_LAMBDA = math.log(2) / 6  # ≈ 0.1155

STORY_WINDOW_HOURS = 48
DEFAULT_LIMIT = 30
MAX_LIMIT = 50
CACHE_TTL = 300  # 5 minutes


def _freshness_decay(published_at: datetime, now: datetime | None = None) -> float:
    """Compute freshness decay factor e^(-λ × hours_age)."""
    if now is None:
        now = datetime.now(UTC)
    # Ensure consistent timezone awareness (SQLite returns naive datetimes)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    age_seconds = (now - published_at).total_seconds()
    hours_age = max(0.0, age_seconds / 3600.0)
    return math.exp(-_LAMBDA * hours_age)


def _authority_multiplier(source_authority: float) -> float:
    """Raw source_authority as the authority multiplier."""
    return source_authority


def _topic_boost(
    story_category: str,
    followed_topics: list[str],
) -> float:
    """10x boost if story category matches any followed topic, else 1x."""
    if not followed_topics:
        return 1.0
    if not story_category:
        return 1.0
    story_cat_lower = story_category.lower()
    for topic in followed_topics:
        if topic.lower() in story_cat_lower or story_cat_lower in topic.lower():
            return 10.0
    return 1.0


def compute_score(
    published_at: datetime,
    source_authority: float,
    story_category: str,
    followed_topics: list[str],
    now: datetime | None = None,
) -> float:
    """Compute a story's ranking score."""
    freshness = _freshness_decay(published_at, now)
    authority = _authority_multiplier(source_authority)
    boost = _topic_boost(story_category, followed_topics)
    return freshness * authority * boost


async def get_ranked_feed(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """Return ranked stories for a user, with Redis caching."""
    limit = min(max(limit, 1), MAX_LIMIT)

    # Check cache
    cache_key = f"feed:{user_id}:v1:{limit}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # Load user preferences
    user = await db.get(UserProfile, user_id)
    if user is None:
        return []

    followed_topics = user.followed_topics or []

    # Query stories from the last 48 hours
    cutoff = datetime.now(UTC)
    stories = await _query_candidate_stories(db, cutoff)

    # Compute scores
    now = datetime.now(UTC)
    scored = []
    for story in stories:
        # Use most recent article's published_at for freshness
        latest_pub = story.get("latest_published_at") or story.get("first_published_at")
        if latest_pub is None:
            continue
        # Use highest authority in the story
        max_authority = story.get("max_authority", 0.5)
        category = story.get("category", "")

        score = compute_score(
            published_at=latest_pub,
            source_authority=max_authority,
            story_category=category,
            followed_topics=followed_topics,
            now=now,
        )

        scored.append(
            {
                "story_id": str(story["story_id"]),
                "canonical_headline": story["canonical_headline"],
                "snippet": story.get("snippet"),
                "source_count": story["article_count"],
                "top_sources": story.get("top_sources", []),
                "category": category,
                "published_at": latest_pub.isoformat(),
                "score": round(score, 6),
                "thumbnail_url": None,
            }
        )

    # Sort by score descending
    scored.sort(key=lambda s: s["score"], reverse=True)

    # Take top N
    result = scored[:limit]

    # Cache
    await cache_set(cache_key, result, ttl=CACHE_TTL)

    return result


async def _query_candidate_stories(
    db: AsyncSession,
    now: datetime,
) -> list[dict]:
    """Query stories with aggregated article stats from the last 48h."""
    cutoff = datetime.fromtimestamp(now.timestamp() - STORY_WINDOW_HOURS * 3600, tz=UTC)

    # Get all stories that have articles published within the window
    subq = (
        select(
            Article.story_id,
            func.max(Article.published_at).label("latest_published_at"),
            func.max(Article.source_authority).label("max_authority"),
        )
        .where(
            Article.story_id.isnot(None),
            Article.published_at >= cutoff,
        )
        .group_by(Article.story_id)
        .subquery()
    )

    stmt = (
        select(
            Story.story_id,
            Story.canonical_headline,
            Story.article_count,
            Story.top_sources,
            Story.category,
            Story.first_published_at,
            subq.c.latest_published_at,
            subq.c.max_authority,
        )
        .join(subq, Story.story_id == subq.c.story_id)
        .order_by(subq.c.latest_published_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "story_id": row.story_id,
            "canonical_headline": row.canonical_headline,
            "article_count": row.article_count,
            "top_sources": list(row.top_sources) if row.top_sources else [],
            "category": row.category,
            "first_published_at": row.first_published_at,
            "latest_published_at": row.latest_published_at,
            "max_authority": row.max_authority or 0.5,
        }
        for row in rows
    ]
