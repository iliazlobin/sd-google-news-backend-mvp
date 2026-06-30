"""Article ORM model with PostgreSQL FTS index."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from google_news.database import Base


class Article(Base):
    __tablename__ = "articles"

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    publisher_domain: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), index=True, nullable=False
    )
    language: Mapped[str] = mapped_column(Text, nullable=False, default="en")
    region: Mapped[str] = mapped_column(Text, nullable=False, default="us")
    source_authority: Mapped[float] = mapped_column(nullable=False, default=0.5)
    story_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("url", name="uq_articles_url"),)
