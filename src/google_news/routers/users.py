"""POST /v1/user/preferences — update user topic/source preferences."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.models.user_profile import UserProfile
from google_news.schemas.user import PreferencesUpdate

router = APIRouter(prefix="/v1", tags=["users"])


@router.post("/user/preferences")
async def update_preferences(
    body: PreferencesUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Upsert user preferences. Returns the full profile."""
    user = await db.get(UserProfile, body.user_id)

    if user is None:
        user = UserProfile(
            user_id=body.user_id,
            followed_topics=body.followed_topics or [],
            followed_sources=body.followed_sources or [],
            region=body.region or "us",
            language_prefs=body.language_prefs or ["en"],
        )
        db.add(user)
    else:
        if body.followed_topics is not None:
            user.followed_topics = body.followed_topics
        if body.followed_sources is not None:
            user.followed_sources = body.followed_sources
        if body.region is not None:
            user.region = body.region
        if body.language_prefs is not None:
            user.language_prefs = body.language_prefs

    await db.commit()
    await db.refresh(user)

    return {
        "user_id": str(user.user_id),
        "followed_topics": list(user.followed_topics or []),
        "followed_sources": list(user.followed_sources or []),
        "region": user.region,
        "language_prefs": list(user.language_prefs or []),
    }
