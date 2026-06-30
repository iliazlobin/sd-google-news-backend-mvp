"""Redis client utility for feed caching."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from google_news.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    """Return a shared Redis connection, or None if unavailable."""
    global _redis
    if _redis is not None:
        try:
            await _redis.ping()
            return _redis
        except Exception:
            _redis = None

    try:
        _redis = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await _redis.ping()
        return _redis
    except Exception:
        logger.warning("Redis unavailable — caching disabled")
        _redis = None
        return None


async def cache_get(key: str) -> Any | None:
    """Get a cached JSON value by key, or None if unavailable/miss."""
    r = await get_redis()
    if r is None:
        return None
    try:
        data = await r.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a cached JSON value with TTL in seconds."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def cache_delete(pattern: str) -> None:
    """Delete all keys matching a pattern."""
    r = await get_redis()
    if r is None:
        return
    try:
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception:
        pass
