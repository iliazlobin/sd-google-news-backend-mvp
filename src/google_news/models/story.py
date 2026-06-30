"""Story ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from google_news.database import Base
from google_news.models._types import StringArray


class Story(Base):
    __tablename__ = "stories"

    story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    canonical_headline: Mapped[str] = mapped_column(sa.Text, nullable=False)
    article_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    top_sources: Mapped[list[str]] = mapped_column(StringArray, nullable=False, default=list)
    category: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    first_published_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
