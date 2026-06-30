"""Functional tests for POST /v1/user/preferences."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_preferences_update_success(client: AsyncClient):
    """Update preferences returns 200 with updated profile."""
    user_id = "00000000-0000-0000-0000-00000000f001"
    prefs = {
        "user_id": user_id,
        "followed_topics": ["sports", "business"],
        "followed_sources": ["espn.com"],
        "region": "us",
        "language_prefs": ["en"],
    }
    r = await client.post("/v1/user/preferences", json=prefs)
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == user_id
    assert set(data["followed_topics"]) == set(prefs["followed_topics"])


@pytest.mark.asyncio
async def test_preferences_partial_update(client: AsyncClient):
    """Partial update preserves unchanged fields."""
    user_id = "00000000-0000-0000-0000-00000000f002"

    # Initial upsert
    await client.post(
        "/v1/user/preferences",
        json={
            "user_id": user_id,
            "followed_topics": ["world"],
            "followed_sources": ["reuters.com"],
            "region": "us",
            "language_prefs": ["en"],
        },
    )

    # Partial update
    r = await client.post(
        "/v1/user/preferences",
        json={
            "user_id": user_id,
            "followed_topics": ["tech"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert set(data["followed_topics"]) == {"tech"}
    assert set(data["followed_sources"]) == {"reuters.com"}
    assert data["region"] == "us"


@pytest.mark.asyncio
async def test_preferences_upsert_new_user(client: AsyncClient):
    """Preferences for new user_id creates profile."""
    new_user = "00000000-0000-0000-0000-00000000f003"
    r = await client.post(
        "/v1/user/preferences",
        json={
            "user_id": new_user,
            "followed_topics": ["tech"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == new_user


@pytest.mark.asyncio
async def test_preferences_missing_user_id_422(client: AsyncClient):
    """Missing user_id returns 422."""
    r = await client.post(
        "/v1/user/preferences",
        json={
            "followed_topics": ["tech"],
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_preferences_invalid_user_id_422(client: AsyncClient):
    """Malformed user_id returns 422."""
    r = await client.post(
        "/v1/user/preferences",
        json={
            "user_id": "not-a-uuid",
            "followed_topics": ["tech"],
        },
    )
    assert r.status_code == 422
