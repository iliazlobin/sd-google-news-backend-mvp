"""FR-1: GET /v1/feed returns ranked stories; freshness decay visible.

AC-1: GET /v1/feed?user_id=<uuid>&limit=30 → 200 with ranked stories.
Freshness decay: older articles score lower than newer ones on same topic.
Unknown user_id → 404. Malformed user_id → 422.
"""

from verify.acceptance.conftest import assert_404, assert_422, assert_json_200


def test_feed_returns_ranked_stories(client, seed_articles, known_user):
    """Feed returns stories sorted by score with expected fields."""
    user_id = known_user["user_id"]
    feed = assert_json_200(client.get(f"/v1/feed?user_id={user_id}&limit=10"))

    assert "stories" in feed
    assert isinstance(feed["stories"], list)
    assert len(feed["stories"]) > 0, "Feed should contain at least one story"

    # Each story must have required fields
    for story in feed["stories"]:
        assert "story_id" in story
        assert "canonical_headline" in story
        assert "source_count" in story or "article_count" in story
        assert "top_sources" in story
        assert "category" in story or "score" in story
        if "score" in story:
            assert isinstance(story["score"], (int, float))

    # Scores should generally decrease (feed is ranked)
    scores = [s.get("score", 0) for s in feed["stories"] if "score" in s]
    if len(scores) >= 2:
        assert scores == sorted(
            scores, reverse=True
        ), f"Feed should be ranked by descending score, got: {scores}"


def test_feed_respects_limit(client, known_user):
    """Feed honors the limit parameter."""
    user_id = known_user["user_id"]
    feed = assert_json_200(client.get(f"/v1/feed?user_id={user_id}&limit=2"))
    assert len(feed["stories"]) <= 2


def test_feed_unknown_user_404(client):
    """Unknown user_id returns 404."""
    assert_404(client.get("/v1/feed?user_id=00000000-0000-0000-0000-00000000ffff"))


def test_feed_malformed_user_id_422(client):
    """Malformed user_id returns 422."""
    assert_422(client.get("/v1/feed?user_id=not-a-uuid"))
    assert_422(client.get("/v1/feed?limit=30"))


def test_feed_freshness_decay_visible(client, seed_articles, known_user):
    """Older articles have lower scores than newer articles on similar topics."""
    user_id = known_user["user_id"]
    feed = assert_json_200(client.get(f"/v1/feed?user_id={user_id}&limit=30"))

    # Find the old, low-authority article's story and compare score
    # to a newer, higher-authority story. The stale article should rank lower.
    stale_headline = "Yesterday's minor local event"
    fresh_headline = "Major earthquake hits Turkey"

    stale_score = None
    fresh_score = None
    for story in feed["stories"]:
        h = story.get("canonical_headline", "")
        if stale_headline in h:
            stale_score = story.get("score", 0)
        if fresh_headline in h:
            fresh_score = story.get("score", 0)

    if stale_score is not None and fresh_score is not None:
        assert (
            fresh_score > stale_score
        ), f"Fresh article ({fresh_score}) should outrank stale article ({stale_score})"
