"""Event logging: fire-and-forget persistence to UserEvent table."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from google_news.models.user_event import UserEvent


async def log_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    story_id: uuid.UUID,
    event_type: str,
) -> uuid.UUID:
    """Persist a single user engagement event.

    Returns the generated event_id. Fire-and-forget — caller doesn't
    need to await the result for correctness.
    """
    event = UserEvent(
        user_id=user_id,
        article_id=article_id,
        story_id=story_id,
        event_type=event_type,
    )
    db.add(event)
    await db.flush()
    return event.event_id
