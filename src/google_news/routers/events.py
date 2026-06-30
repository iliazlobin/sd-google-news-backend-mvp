"""POST /v1/events — log user engagement (fire-and-forget)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.database import get_db
from google_news.schemas.event import EventCreate
from google_news.services.event_service import log_event

router = APIRouter(prefix="/v1", tags=["events"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a user engagement event. Fire-and-forget — always 202."""
    event_id = await log_event(
        db,
        user_id=body.user_id,
        article_id=body.article_id,
        story_id=body.story_id,
        event_type=body.event_type,
    )
    await db.commit()

    return {
        "status": "accepted",
        "event_id": str(event_id),
    }
