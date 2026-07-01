"""Shared fixtures and helpers for the black-box acceptance suite.

These tests do NOT import `src.google_news`. They talk to the running system
via HTTP at API_BASE_URL.
"""

import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ── Dynamic timestamp helpers ───────────────────────────────────────
# All seed timestamps are computed relative to now so they never go stale
# (the feed has a 48h window; hardcoded dates eventually fall outside it).


def _rel(hours_ago: float) -> str:
    """Return an ISO-8601 timestamp `hours_ago` hours before now."""
    dt = datetime.now(UTC) - timedelta(hours=hours_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture(scope="session")
def base_url() -> str:
    return API_BASE_URL


@pytest.fixture(scope="session")
def client(base_url: str):
    """Session-scoped httpx client for the entire acceptance run."""
    with httpx.Client(base_url=base_url, timeout=10) as c:
        yield c


@pytest.fixture
def seed_articles(client):
    """Ingest a batch of articles and return their response data.

    Timestamps are relative to now so the feed 48h window never expires.
    Returns a list of (article_id, story_id, headline, published_at,
    source_authority, publisher_domain).
    """
    articles_data = [
        {
            "url": "https://reuters.com/quake-turkey-2026",
            "headline": "Major earthquake hits Turkey, thousands displaced",
            "snippet": "A 7.2 magnitude earthquake struck eastern Turkey early Monday, collapsing buildings and displacing thousands.",
            "publisher_domain": "reuters.com",
            "published_at": _rel(2.0),
            "language": "en",
            "region": "world",
            "source_authority": 0.95,
        },
        {
            "url": "https://bbc.com/quake-turkey-2026",
            "headline": "Turkey earthquake: rescue efforts underway as death toll rises",
            "snippet": "Rescue teams are working through the night in eastern Turkey after a devastating 7.2 magnitude earthquake.",
            "publisher_domain": "bbc.com",
            "published_at": _rel(1.5),
            "language": "en",
            "region": "world",
            "source_authority": 0.90,
        },
        {
            "url": "https://techcrunch.com/ai-chip-launch-2026",
            "headline": "New AI chip startup raises $500M in Series C",
            "snippet": "A stealth-mode AI chip startup announced a $500M Series C round led by major VCs, aiming to compete with NVIDIA.",
            "publisher_domain": "techcrunch.com",
            "published_at": _rel(1.0),
            "language": "en",
            "region": "us",
            "source_authority": 0.80,
        },
        {
            "url": "https://theverge.com/ai-chip-launch-2026",
            "headline": "This new AI chip company just raised $500M to challenge NVIDIA",
            "snippet": "The AI hardware space is heating up as a new challenger raises half a billion dollars to take on the GPU giant.",
            "publisher_domain": "theverge.com",
            "published_at": _rel(0.5),
            "language": "en",
            "region": "us",
            "source_authority": 0.75,
        },
        {
            "url": "https://espn.com/world-cup-final-2026",
            "headline": "World Cup final ends in dramatic penalty shootout",
            "snippet": "The 2026 World Cup final went to penalties after a 2-2 draw, with the underdogs claiming their first title.",
            "publisher_domain": "espn.com",
            "published_at": _rel(3.0),
            "language": "en",
            "region": "us",
            "source_authority": 0.85,
        },
        {
            "url": "https://old-news.com/stale-article-2026",
            "headline": "Yesterday's minor local event",
            "snippet": "A small community event took place yesterday with minimal turnout.",
            "publisher_domain": "old-news.com",
            "published_at": _rel(25.0),
            "language": "en",
            "region": "local",
            "source_authority": 0.20,
        },
    ]

    ingested = []
    for art in articles_data:
        r = client.post("/v1/articles", json=art)
        if r.status_code in (201, 409):
            ingested.append(r.json())
    return ingested


@pytest.fixture
def known_user(client):
    """Create or upsert a user with known preferences, return user_id."""
    user_body = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "followed_topics": ["world", "tech"],
        "followed_sources": ["reuters.com"],
        "region": "us",
        "language_prefs": ["en"],
    }
    r = client.post("/v1/user/preferences", json=user_body)
    assert r.status_code == 200
    return r.json()


# ── Assertion helpers ──────────────────────────────────────────────


def assert_json_200(r, expected_status=200):
    """Assert status and return parsed JSON."""
    assert (
        r.status_code == expected_status
    ), f"Expected {expected_status}, got {r.status_code}: {r.text}"
    return r.json()


def assert_201(r):
    return assert_json_200(r, 201)


def assert_202(r):
    return assert_json_200(r, 202)


def assert_404(r):
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
    return r.json()


def assert_409(r):
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    return r.json()


def assert_422(r):
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    return r.json()
