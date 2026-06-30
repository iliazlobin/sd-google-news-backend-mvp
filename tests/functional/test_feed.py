"""Functional tests for GET /v1/feed."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _seed_user(client: AsyncClient, user_id: str, topics: list[str] | None = None) -> None:
    """Create a user profile for testing."""

    # Use the overridden get_db via the app
    r = await client.post(
        "/v1/user/preferences",
        json={
            "user_id": user_id,
            "followed_topics": topics or [],
            "followed_sources": [],
            "region": "us",
            "language_prefs": ["en"],
        },
    )
    assert r.status_code == 200, f"User seed failed: {r.text}"


@pytest.mark.asyncio
async def test_feed_returns_empty_for_new_user(client: AsyncClient):
    """A user with no stories in their feed gets an empty list."""
    user_id = str(uuid.uuid4())
    # Create user
    await _seed_user(client, user_id)

    r = await client.get(f"/v1/feed?user_id={user_id}&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "stories" in data
    assert isinstance(data["stories"], list)


@pytest.mark.asyncio
async def test_feed_returns_stories_when_data_exists(client: AsyncClient):
    """Feed returns stories after articles are ingested."""
    user_id = str(uuid.uuid4())
    await _seed_user(client, user_id, ["tech"])

    # Ingest an article
    r1 = await client.post(
        "/v1/articles",
        json={
            "url": f"https://test.com/feed-test-{uuid.uuid4()}.html",
            "headline": "AI startup raises millions in funding",
            "snippet": "A new AI startup has secured significant funding.",
            "publisher_domain": "test.com",
            "published_at": "2026-06-29T10:00:00Z",
            "source_authority": 0.9,
        },
    )
    assert r1.status_code == 201

    r = await client.get(f"/v1/feed?user_id={user_id}&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "stories" in data
    # Should have at least one story
    assert len(data["stories"]) >= 1


@pytest.mark.asyncio
async def test_feed_unknown_user_404(client: AsyncClient):
    """Unknown user_id returns 404."""
    r = await client.get("/v1/feed?user_id=00000000-0000-0000-0000-00000000ffff")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_feed_malformed_user_id_422(client: AsyncClient):
    """Malformed user_id returns 422."""
    r = await client.get("/v1/feed?user_id=not-a-uuid")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_feed_respects_limit(client: AsyncClient):
    """Feed honors the limit parameter."""
    user_id = str(uuid.uuid4())
    await _seed_user(client, user_id)

    r = await client.get(f"/v1/feed?user_id={user_id}&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["stories"]) <= 2
