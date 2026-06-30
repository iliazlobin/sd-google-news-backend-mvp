"""Functional tests for POST /v1/events."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def _ingest_article(client: AsyncClient) -> dict:
    """Ingest a test article and return the response."""
    r = await client.post(
        "/v1/articles",
        json={
            "url": f"https://event-test.com/art-{uuid.uuid4()}.html",
            "headline": "Event test article",
            "publisher_domain": "event-test.com",
            "published_at": "2026-06-29T10:00:00Z",
        },
    )
    assert r.status_code == 201
    return r.json()


@pytest.mark.asyncio
async def test_event_accepted_202(client: AsyncClient):
    """Posting an event returns 202 Accepted with event_id."""
    art = await _ingest_article(client)
    user_id = "00000000-0000-0000-0000-00000000e001"

    r = await client.post(
        "/v1/events",
        json={
            "user_id": user_id,
            "article_id": art["article_id"],
            "story_id": art["story_id"],
            "event_type": "click",
        },
    )
    assert r.status_code == 202
    data = r.json()
    assert "event_id" in data
    uuid.UUID(data["event_id"])


@pytest.mark.asyncio
async def test_event_all_types_accepted(client: AsyncClient):
    """All valid event types are accepted."""
    art = await _ingest_article(client)
    user_id = "00000000-0000-0000-0000-00000000e002"

    for event_type in ("impression", "click", "long_dwell", "dismiss"):
        r = await client.post(
            "/v1/events",
            json={
                "user_id": user_id,
                "article_id": art["article_id"],
                "story_id": art["story_id"],
                "event_type": event_type,
            },
        )
        assert r.status_code == 202


@pytest.mark.asyncio
async def test_event_duplicate_accepted(client: AsyncClient):
    """Duplicate events are accepted (fire-and-forget)."""
    art = await _ingest_article(client)
    user_id = "00000000-0000-0000-0000-00000000e003"

    body = {
        "user_id": user_id,
        "article_id": art["article_id"],
        "story_id": art["story_id"],
        "event_type": "impression",
    }
    r1 = await client.post("/v1/events", json=body)
    r2 = await client.post("/v1/events", json=body)
    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r1.json()["event_id"] != r2.json()["event_id"]


@pytest.mark.asyncio
async def test_event_invalid_type_422(client: AsyncClient):
    """Invalid event_type returns 422."""
    art = await _ingest_article(client)
    r = await client.post(
        "/v1/events",
        json={
            "user_id": "00000000-0000-0000-0000-00000000e004",
            "article_id": art["article_id"],
            "story_id": art["story_id"],
            "event_type": "invalid_type",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_event_missing_required_fields_422(client: AsyncClient):
    """Missing required fields returns 422."""
    art = await _ingest_article(client)

    # Missing user_id
    r = await client.post(
        "/v1/events",
        json={
            "article_id": art["article_id"],
            "story_id": art["story_id"],
            "event_type": "click",
        },
    )
    assert r.status_code == 422

    # Missing event_type
    r = await client.post(
        "/v1/events",
        json={
            "user_id": "00000000-0000-0000-0000-00000000e005",
            "article_id": art["article_id"],
            "story_id": art["story_id"],
        },
    )
    assert r.status_code == 422
