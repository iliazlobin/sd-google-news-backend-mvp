"""Functional tests for GET /v1/search."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_missing_query_422(client: AsyncClient):
    """Missing query parameter returns 422."""
    r = await client.get("/v1/search?limit=10")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_search_empty_query_422(client: AsyncClient):
    """Empty query returns 422."""
    r = await client.get("/v1/search?q=&limit=10")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_search_no_match_returns_empty(client: AsyncClient):
    """Search with no matching query returns empty results (200)."""
    r = await client.get("/v1/search?q=xyznonexistentfoobar12345&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert data["results"] == []
    assert data.get("total", 0) == 0


@pytest.mark.asyncio
async def test_search_returns_matching_articles(client: AsyncClient):
    """Search for keyword returns relevant articles."""
    # Ingest an article first
    await client.post(
        "/v1/articles",
        json={
            "url": f"https://search-test.com/article-{uuid.uuid4()}.html",
            "headline": "Earthquake hits coastal region causing damage",
            "snippet": "A powerful earthquake struck the coastal area today.",
            "publisher_domain": "search-test.com",
            "published_at": "2026-06-29T10:00:00Z",
        },
    )

    r = await client.get("/v1/search?q=earthquake&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    # On SQLite, ILIKE fallback should find the article
    assert len(data["results"]) >= 1
    assert "headline" in data["results"][0]


@pytest.mark.asyncio
async def test_search_respects_limit(client: AsyncClient):
    """Search honors the limit parameter."""
    # Ingest multiple articles
    for i in range(3):
        await client.post(
            "/v1/articles",
            json={
                "url": f"https://search-test.com/limit-{i}-{uuid.uuid4()}.html",
                "headline": f"Technology breakthrough number {i}",
                "publisher_domain": "search-test.com",
                "published_at": "2026-06-29T10:00:00Z",
            },
        )

    r = await client.get("/v1/search?q=technology&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) <= 2
