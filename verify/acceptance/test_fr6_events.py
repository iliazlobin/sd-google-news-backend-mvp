"""FR-6: POST /v1/events accepts events (202); events persist.

AC-6: Post engagement event → 202 Accepted. Event can be retrieved or
duplicate events are accepted (idempotent fire-and-forget). Invalid event_type → 422.
"""

import uuid

from verify.acceptance.conftest import assert_202, assert_422, assert_json_200


def test_event_accepted_202(client, seed_articles):
    """Posting an event returns 202 Accepted with event_id."""
    # Pick an article_id from seed data
    article_ids = [a.get("article_id") for a in seed_articles if a.get("article_id")]
    story_ids = [a.get("story_id") for a in seed_articles if a.get("story_id")]
    assert article_ids, "Need at least one article from seed data"

    user_id = "00000000-0000-0000-0000-000000000001"
    event = {
        "user_id": user_id,
        "article_id": article_ids[0],
        "story_id": story_ids[0] if story_ids else article_ids[0],
        "event_type": "click",
    }

    resp = assert_202(client.post("/v1/events", json=event))
    assert "event_id" in resp
    uuid.UUID(resp["event_id"])


def test_event_all_types_accepted(client, seed_articles):
    """All valid event types are accepted."""
    article_ids = [a.get("article_id") for a in seed_articles if a.get("article_id")]
    story_ids = [a.get("story_id") for a in seed_articles if a.get("story_id")]
    assert article_ids, "Need at least one article"

    user_id = "00000000-0000-0000-0000-00000000e002"
    for event_type in ("impression", "click", "long_dwell", "dismiss"):
        resp = assert_202(
            client.post(
                "/v1/events",
                json={
                    "user_id": user_id,
                    "article_id": article_ids[0],
                    "story_id": story_ids[0] if story_ids else article_ids[0],
                    "event_type": event_type,
                },
            )
        )
        assert "event_id" in resp


def test_event_duplicate_accepted(client, seed_articles):
    """Duplicate events are accepted (fire-and-forget, each gets a new event_id)."""
    article_ids = [a.get("article_id") for a in seed_articles if a.get("article_id")]
    story_ids = [a.get("story_id") for a in seed_articles if a.get("story_id")]
    assert article_ids, "Need at least one article"

    user_id = "00000000-0000-0000-0000-00000000e003"
    event_body = {
        "user_id": user_id,
        "article_id": article_ids[0],
        "story_id": story_ids[0] if story_ids else article_ids[0],
        "event_type": "impression",
    }

    first = assert_202(client.post("/v1/events", json=event_body))
    second = assert_202(client.post("/v1/events", json=event_body))

    # Each should get a unique event_id
    assert first["event_id"] != second["event_id"]


def test_event_invalid_type_422(client, seed_articles):
    """Invalid event_type returns 422."""
    article_ids = [a.get("article_id") for a in seed_articles if a.get("article_id")]
    story_ids = [a.get("story_id") for a in seed_articles if a.get("story_id")]
    assert article_ids, "Need at least one article"

    assert_422(
        client.post(
            "/v1/events",
            json={
                "user_id": "00000000-0000-0000-0000-00000000e004",
                "article_id": article_ids[0],
                "story_id": story_ids[0] if story_ids else article_ids[0],
                "event_type": "invalid_type",
            },
        )
    )


def test_event_missing_required_fields_422(client, seed_articles):
    """Missing required fields returns 422."""
    article_ids = [a.get("article_id") for a in seed_articles if a.get("article_id")]
    assert article_ids, "Need at least one article"

    # Missing user_id
    assert_422(
        client.post(
            "/v1/events",
            json={
                "article_id": article_ids[0],
                "story_id": article_ids[0],
                "event_type": "click",
            },
        )
    )

    # Missing event_type
    assert_422(
        client.post(
            "/v1/events",
            json={
                "user_id": "00000000-0000-0000-0000-00000000e005",
                "article_id": article_ids[0],
                "story_id": article_ids[0],
            },
        )
    )
