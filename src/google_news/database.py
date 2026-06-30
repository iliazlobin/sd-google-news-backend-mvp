"""Async database engine, session factory, and FastAPI dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from google_news.config import settings

_engine = None
_session_factory = None


def get_engine():
    """Lazily create and return the async engine."""
    global _engine
    if _engine is None:
        url = settings.database_url
        extra: dict = {}
        # SQLite needs aiosqlite driver; check_url does not need special casing
        # beyond the URL scheme, but create_async_engine handles it.
        if url.startswith("sqlite"):
            extra["connect_args"] = {"check_same_thread": False}
        _engine = create_async_engine(
            url,
            echo=(settings.log_level == "debug"),
            **extra,
        )
    return _engine


def get_session_factory():
    """Lazily create and return the async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session and closes it after."""
    async with get_session_factory()() as session:
        try:
            yield session
        finally:
            await session.close()
