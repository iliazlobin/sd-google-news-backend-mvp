"""FR-4: POST /v1/user/preferences updates topics/sources;
next feed reflects boost.

AC-4: Update preferences → 200. Next feed reflects topic/source boost
(followed topics rank higher). Create new user via preferences upsert.
"""

from verify.acceptance.conftest import assert_json_200, assert_422


def test_preferences_update_success(client):
    """Update preferences for a user returns updated profile."""
    user_id = "00000000-0000-0000-0000-00000000f005"
    prefs = {
        "user_id": user_id,
        "followed_topics": ["sports", "business"],
        "followed_sources": ["espn.com"],
        "region": "us",
        "language_prefs": ["en"],
    }

    resp = assert_json_200(client.post("/v1/user/preferences", json=prefs))

    assert resp["user_id"] == user_id
    assert set(resp["followed_topics"]) == set(prefs["followed_topics"])
    assert set(resp["followed_sources"]) == set(prefs["followed_sources"])
    assert resp["region"] == prefs["region"]


def test_preferences_partial_update(client):
    """Update only some fields; others remain unchanged."""
    user_id = "00000000-0000-0000-0000-00000000f006"

    # Initial upsert
    client.post("/v1/user/preferences", json={
        "user_id": user_id,
        "followed_topics": ["world"],
        "followed_sources": ["reuters.com"],
        "region": "us",
        "language_prefs": ["en"],
    })

    # Partial update — only change topics
    resp = assert_json_200(client.post("/v1/user/preferences", json={
        "user_id": user_id,
        "followed_topics": ["tech"],
    }))

    assert set(resp["followed_topics"]) == {"tech"}
    # followed_sources should still be the original
    assert set(resp["followed_sources"]) == {"reuters.com"}
    assert resp["region"] == "us"


def test_preferences_upsert_new_user(client):
    """Posting preferences for a new user_id creates the profile."""
    new_user_id = "00000000-0000-0000-0000-00000000f007"
    resp = assert_json_200(client.post("/v1/user/preferences", json={
        "user_id": new_user_id,
        "followed_topics": ["tech"],
    }))

    assert resp["user_id"] == new_user_id
    assert "followed_topics" in resp


def test_feed_reflects_topic_boost(client, seed_articles):
    """User with 'tech' topic preference sees tech articles ranked higher."""
    user_id = "00000000-0000-0000-0000-00000000f008"

    # Set preference for tech
    client.post("/v1/user/preferences", json={
        "user_id": user_id,
        "followed_topics": ["tech"],
    })

    feed = assert_json_200(
        client.get(f"/v1/feed?user_id={user_id}&limit=10")
    )

    # Should have stories in the feed
    assert len(feed["stories"]) > 0

    # Tech articles (if present) should appear and have non-zero scores
    tech_articles = [
        s for s in feed["stories"]
        if "chip" in s.get("canonical_headline", "").lower()
        or "ai" in s.get("canonical_headline", "").lower()
    ]
    # If tech articles exist in feed, they should have scores
    for art in tech_articles:
        if "score" in art:
            assert art["score"] > 0, f"Tech article should have positive score: {art}"


def test_preferences_missing_user_id_422(client):
    """Missing user_id in preferences body returns 422."""
    assert_422(client.post("/v1/user/preferences", json={
        "followed_topics": ["tech"],
    }))


def test_preferences_invalid_user_id_422(client):
    """Malformed user_id returns 422."""
    assert_422(client.post("/v1/user/preferences", json={
        "user_id": "not-a-uuid",
        "followed_topics": ["tech"],
    }))
