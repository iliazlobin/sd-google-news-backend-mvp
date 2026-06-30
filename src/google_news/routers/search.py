"""GET /v1/search — full-text article search."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.services.search_service import search_articles, search_count

router = APIRouter(prefix="/v1", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across articles with optional time-range filter."""
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "Query parameter 'q' is required"},
        )

    results = await search_articles(db, q, from_date, to_date, limit)
    total = await search_count(db, q, from_date, to_date)

    return {
        "results": results,
        "query": q.strip(),
        "total": total,
    }
