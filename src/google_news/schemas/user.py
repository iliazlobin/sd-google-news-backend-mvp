"""User preference schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class PreferencesUpdate(BaseModel):
    """Payload for POST /v1/user/preferences."""

    user_id: uuid.UUID
    followed_topics: list[str] | None = Field(None, max_length=50)
    followed_sources: list[str] | None = Field(None, max_length=50)
    region: str | None = Field(None, min_length=2, max_length=5)
    language_prefs: list[str] | None = Field(None, max_length=10)


class PreferencesResponse(BaseModel):
    """Response for user preferences."""

    user_id: uuid.UUID
    followed_topics: list[str]
    followed_sources: list[str]
    region: str
    language_prefs: list[str]

    model_config = {"from_attributes": True}
