"""PostgreSQL full-text search via tsvector/tsquery with SQLite fallback."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.models.article import Article


async def search_articles(
    db: AsyncSession,
    query: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 20,
) -> list[dict]:
    """Full-text search across articles with optional time-range filter.

    Uses PostgreSQL tsvector/tsquery when available; falls back to ILIKE on SQLite.
    """
    query = query.strip()
    if not query:
        return []

    limit = min(max(limit, 1), 50)

    engine = db.get_bind()
    dialect_name = engine.dialect.name if engine else "postgresql"

    if dialect_name == "postgresql":
        return await _search_postgresql(db, query, from_date, to_date, limit)
    else:
        return await _search_sqlite(db, query, from_date, to_date, limit)


async def _search_postgresql(
    db: AsyncSession,
    query: str,
    from_date: datetime | None,
    to_date: datetime | None,
    limit: int,
) -> list[dict]:
    """PostgreSQL tsvector + ts_rank search."""
    ts_query = func.plainto_tsquery(text("'english'"), query)
    rank = func.ts_rank(
        func.to_tsvector(
            text("'english'"),
            Article.headline + text("' '") + func.coalesce(Article.snippet, text("''")),
        ),
        ts_query,
    ).label("relevance")

    conditions = [
        func.to_tsvector(
            text("'english'"),
            Article.headline + text("' '") + func.coalesce(Article.snippet, text("''")),
        ).op("@@")(ts_query),
    ]
    if from_date is not None:
        conditions.append(Article.published_at >= from_date)
    if to_date is not None:
        conditions.append(Article.published_at <= to_date)

    stmt = (
        select(
            Article.article_id,
            Article.story_id,
            Article.headline,
            Article.snippet,
            Article.publisher_domain,
            Article.published_at,
            rank,
        )
        .where(*conditions)
        .order_by(rank.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "article_id": str(row.article_id),
            "story_id": str(row.story_id) if row.story_id else None,
            "headline": row.headline,
            "snippet": row.snippet,
            "publisher_domain": row.publisher_domain,
            "published_at": row.published_at.isoformat(),
            "relevance": round(float(row.relevance), 6),
        }
        for row in rows
    ]


async def _search_sqlite(
    db: AsyncSession,
    query: str,
    from_date: datetime | None,
    to_date: datetime | None,
    limit: int,
) -> list[dict]:
    """SQLite fallback using ILIKE."""
    like_pattern = f"%{query}%"
    conditions: list = [
        Article.headline.ilike(like_pattern) | Article.snippet.ilike(like_pattern),
    ]
    if from_date is not None:
        conditions.append(Article.published_at >= from_date)
    if to_date is not None:
        conditions.append(Article.published_at <= to_date)

    stmt = (
        select(
            Article.article_id,
            Article.story_id,
            Article.headline,
            Article.snippet,
            Article.publisher_domain,
            Article.published_at,
            literal_column("1.0").label("relevance"),
        )
        .where(*conditions)
        .order_by(Article.published_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "article_id": str(row.article_id),
            "story_id": str(row.story_id) if row.story_id else None,
            "headline": row.headline,
            "snippet": row.snippet,
            "publisher_domain": row.publisher_domain,
            "published_at": row.published_at.isoformat(),
            "relevance": 1.0,
        }
        for row in rows
    ]


async def search_count(
    db: AsyncSession,
    query: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> int:
    """Count matching articles for search total."""
    engine = db.get_bind()
    dialect_name = engine.dialect.name if engine else "postgresql"

    if dialect_name == "postgresql":
        ts_query = func.plainto_tsquery(text("'english'"), query)
        conditions = [
            func.to_tsvector(
                text("'english'"),
                Article.headline + text("' '") + func.coalesce(Article.snippet, text("''")),
            ).op("@@")(ts_query),
        ]
    else:
        like_pattern = f"%{query}%"
        conditions = [
            Article.headline.ilike(like_pattern) | Article.snippet.ilike(like_pattern),
        ]

    if from_date is not None:
        conditions.append(Article.published_at >= from_date)
    if to_date is not None:
        conditions.append(Article.published_at <= to_date)

    stmt = select(func.count()).select_from(Article).where(*conditions)
    result = await db.execute(stmt)
    return result.scalar() or 0
