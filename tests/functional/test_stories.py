"""Functional tests for GET /v1/stories endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_story_detail_unknown_404(client: AsyncClient):
    """Unknown story_id returns 404."""
    r = await client.get("/v1/stories/00000000-0000-0000-0000-00000000dead")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_story_detail_after_ingest(client: AsyncClient):
    """Story detail returns correct data after article ingest."""
    # Ingest an article to create a story
    r1 = await client.post(
        "/v1/articles",
        json={
            "url": f"https://story-test.com/detail-{uuid.uuid4()}.html",
            "headline": "Story detail test article",
            "publisher_domain": "story-test.com",
            "published_at": "2026-06-29T10:00:00Z",
            "source_authority": 0.85,
        },
    )
    assert r1.status_code == 201
    story_id = r1.json()["story_id"]

    r = await client.get(f"/v1/stories/{story_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["story_id"] == story_id
    assert "canonical_headline" in data
    assert "article_count" in data
    assert data["article_count"] >= 1
    assert "top_sources" in data


@pytest.mark.asyncio
async def test_story_articles_paginated(client: AsyncClient):
    """GET /v1/stories/{id}/articles returns paginated results."""
    # Ingest article
    r1 = await client.post(
        "/v1/articles",
        json={
            "url": f"https://story-test.com/paged-{uuid.uuid4()}.html",
            "headline": "Pagination test article",
            "publisher_domain": "story-test.com",
            "published_at": "2026-06-29T10:00:00Z",
        },
    )
    assert r1.status_code == 201
    story_id = r1.json()["story_id"]

    r = await client.get(f"/v1/stories/{story_id}/articles?limit=1&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["story_id"] == story_id
    assert "articles" in data
    assert "total" in data
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert isinstance(data["articles"], list)
    if data["articles"]:
        art = data["articles"][0]
        assert "article_id" in art
        assert "headline" in art
        assert "publisher_domain" in art


@pytest.mark.asyncio
async def test_story_articles_unknown_story_404(client: AsyncClient):
    """Articles sub-resource on unknown story returns 404."""
    r = await client.get("/v1/stories/00000000-0000-0000-0000-00000000dead/articles")
    assert r.status_code == 404
