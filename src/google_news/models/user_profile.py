"""UserProfile ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from google_news.database import Base
from google_news.models._types import StringArray


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    followed_topics: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    followed_sources: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    region: Mapped[str] = mapped_column(sa.Text, nullable=False, default="us")
    language_prefs: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
