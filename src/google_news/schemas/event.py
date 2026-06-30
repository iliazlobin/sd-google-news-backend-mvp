"""Event schemas."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Payload for POST /v1/events."""

    user_id: uuid.UUID
    article_id: uuid.UUID
    story_id: uuid.UUID
    event_type: Literal["impression", "click", "long_dwell", "dismiss"]


class EventResponse(BaseModel):
    """Response for POST /v1/events (202 Accepted)."""

    status: str = "accepted"
    event_id: uuid.UUID
