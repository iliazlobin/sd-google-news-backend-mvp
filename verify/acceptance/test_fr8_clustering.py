"""FR-8: Two articles with similar text get same story_id (clustering works).

AC-8: Ingest two articles about the same topic → both assigned to the same story_id.
Ingest an unrelated article → different story_id.
"""

import uuid

from verify.acceptance.conftest import assert_201


def test_similar_articles_get_same_story(client):
    """Two articles about the same event share a story_id."""
    # First article about an earthquake event
    url1 = f"https://news-site-a.com/quake-{uuid.uuid4()}.html"
    art1 = {
        "url": url1,
        "headline": "Powerful earthquake shakes coastal region",
        "snippet": "A powerful 6.8 magnitude earthquake struck the coastal region today, causing widespread damage and triggering tsunami warnings.",
        "publisher_domain": "news-site-a.com",
        "published_at": "2026-06-29T14:00:00Z",
        "language": "en",
        "region": "world",
        "source_authority": 0.85,
    }
    resp1 = assert_201(client.post("/v1/articles", json=art1))
    story_id_1 = resp1["story_id"]

    # Second article about the same event, different wording
    url2 = f"https://news-site-b.com/quake-{uuid.uuid4()}.html"
    art2 = {
        "url": url2,
        "headline": "Tsunami warning issued after magnitude 6.8 quake hits coast",
        "snippet": "Authorities have issued a tsunami warning following a 6.8 magnitude earthquake that struck the coastal region, with reports of significant structural damage.",
        "publisher_domain": "news-site-b.com",
        "published_at": "2026-06-29T14:05:00Z",
        "language": "en",
        "region": "world",
        "source_authority": 0.80,
    }
    resp2 = assert_201(client.post("/v1/articles", json=art2))
    story_id_2 = resp2["story_id"]

    assert story_id_1 == story_id_2, (
        f"Similar articles should get same story_id, "
        f"got {story_id_1} and {story_id_2}"
    )


def test_dissimilar_articles_get_different_stories(client):
    """Two articles about different topics get different story_ids."""
    # Article about sports
    url3 = f"https://sports-site.com/game-{uuid.uuid4()}.html"
    resp3 = assert_201(client.post("/v1/articles", json={
        "url": url3,
        "headline": "Championship game ends in stunning upset",
        "snippet": "The underdog team pulled off a stunning victory in the championship game, beating the defending champions in a last-minute play.",
        "publisher_domain": "sports-site.com",
        "published_at": "2026-06-29T15:00:00Z",
        "language": "en",
        "region": "us",
        "source_authority": 0.80,
    }))
    sports_story_id = resp3["story_id"]

    # Article about technology
    url4 = f"https://tech-site.com/launch-{uuid.uuid4()}.html"
    resp4 = assert_201(client.post("/v1/articles", json={
        "url": url4,
        "headline": "Tech giant unveils revolutionary new device",
        "snippet": "The company's latest product launch features breakthrough technology in battery life and display quality, setting new industry standards.",
        "publisher_domain": "tech-site.com",
        "published_at": "2026-06-29T15:30:00Z",
        "language": "en",
        "region": "us",
        "source_authority": 0.85,
    }))
    tech_story_id = resp4["story_id"]

    assert sports_story_id != tech_story_id, (
        "Unrelated articles should get different story_ids"
    )


def test_clustering_triggers_on_ingest(client):
    """Ingesting an article triggers clustering — it always gets a story_id."""
    url = f"https://standalone-news.com/solo-{uuid.uuid4()}.html"
    resp = assert_201(client.post("/v1/articles", json={
        "url": url,
        "headline": "A unique standalone news story with no peers",
        "snippet": "This is a completely unique article about an event no one else is covering.",
        "publisher_domain": "standalone-news.com",
        "published_at": "2026-06-29T16:00:00Z",
        "language": "en",
        "region": "world",
        "source_authority": 0.50,
    }))

    # Even a standalone article gets a story (its own, new story)
    assert "story_id" in resp
    uuid.UUID(resp["story_id"])
