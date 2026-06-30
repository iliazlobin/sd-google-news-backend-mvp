"""Unit tests for the Google News MVP application."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_returns_200(client: AsyncClient):
    """The /healthz endpoint returns 200 OK with expected payload."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_openapi_schema_accessible(client: AsyncClient):
    """The OpenAPI schema is served at /openapi.json."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Google News MVP"
    assert "/healthz" in data["paths"]
