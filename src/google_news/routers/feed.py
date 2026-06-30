"""GET /v1/feed — ranked story feed for a user."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.models.user_profile import UserProfile
from google_news.services.feed_service import DEFAULT_LIMIT, MAX_LIMIT, get_ranked_feed

router = APIRouter(prefix="/v1", tags=["feed"])


@router.get("/feed")
async def get_feed(
    user_id: uuid.UUID = Query(..., description="User ID"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
):
    """Get a ranked story feed for a user."""
    # Check user exists
    user = await db.get(UserProfile, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": f"User {user_id} not found"},
        )

    stories = await get_ranked_feed(db, user_id, limit)

    return {
        "stories": stories,
        "user_id": str(user_id),
    }
