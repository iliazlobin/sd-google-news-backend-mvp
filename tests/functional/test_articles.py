"""Functional tests for article ingestion (POST /v1/articles)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_article_201(client: AsyncClient):
    """Ingesting a new article returns 201 with article_id and story_id."""
    unique_url = f"https://test-news.com/article-{uuid.uuid4()}.html"
    article = {
        "url": unique_url,
        "headline": "Test: new scientific breakthrough announced",
        "publisher_domain": "test-news.com",
        "published_at": "2026-06-29T10:00:00Z",
        "language": "en",
        "region": "world",
        "source_authority": 0.70,
    }
    response = await client.post("/v1/articles", json=article)
    assert response.status_code == 201
    data = response.json()
    assert "article_id" in data
    assert "story_id" in data
    uuid.UUID(data["article_id"])
    uuid.UUID(data["story_id"])


@pytest.mark.asyncio
async def test_ingest_article_duplicate_url_409(client: AsyncClient):
    """Duplicate URL returns 409 with existing_article_id."""
    dup_url = f"https://dup-test.com/dup-{uuid.uuid4()}.html"
    article = {
        "url": dup_url,
        "headline": "Duplicate test article",
        "publisher_domain": "dup-test.com",
        "published_at": "2026-06-29T10:00:00Z",
    }

    # First ingest succeeds
    r1 = await client.post("/v1/articles", json=article)
    assert r1.status_code == 201

    # Second ingest with same URL → 409
    r2 = await client.post("/v1/articles", json=article)
    assert r2.status_code == 409
    data = r2.json()
    assert "detail" in data or "existing_article_id" in data


@pytest.mark.asyncio
async def test_ingest_article_missing_required_fields_422(client: AsyncClient):
    """Missing headline returns 422."""
    r = await client.post(
        "/v1/articles",
        json={
            "url": f"https://bad.com/missing-{uuid.uuid4()}.html",
            "publisher_domain": "bad.com",
            "published_at": "2026-06-29T10:00:00Z",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_article_missing_url_422(client: AsyncClient):
    """Missing url returns 422."""
    r = await client.post(
        "/v1/articles",
        json={
            "headline": "No URL article",
            "publisher_domain": "bad.com",
            "published_at": "2026-06-29T10:00:00Z",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_article_minimal_fields_201(client: AsyncClient):
    """Ingest with only required fields works."""
    url = f"https://minimal-news.com/min-{uuid.uuid4()}.html"
    article = {
        "url": url,
        "headline": "Minimal article for testing",
        "publisher_domain": "minimal-news.com",
        "published_at": "2026-06-29T10:00:00Z",
    }
    r = await client.post("/v1/articles", json=article)
    assert r.status_code == 201
    data = r.json()
    assert "article_id" in data
    assert "story_id" in data
