"""FR-2: GET /v1/stories/{id} returns canonical headline + top sources;
GET /v1/stories/{id}/articles paginates.

AC-2: Story detail: 200 with headline + source attribution. 404 on unknown story.
Articles sub-resource: paginated with limit/offset, 404 on unknown story.
"""

from verify.acceptance.conftest import assert_json_200, assert_404


def test_story_detail_success(client, seed_articles):
    """Story detail returns canonical headline, top sources, article count."""
    # Get a story_id from ingested articles
    story_ids = {
        a.get("story_id") for a in seed_articles if a.get("story_id")
    }
    assert story_ids, "Need at least one story from seed data"
    story_id = list(story_ids)[0]

    detail = assert_json_200(client.get(f"/v1/stories/{story_id}"))

    assert detail["story_id"] == story_id
    assert "canonical_headline" in detail
    assert len(detail["canonical_headline"]) > 0
    assert "article_count" in detail
    assert isinstance(detail["article_count"], int)
    assert detail["article_count"] >= 1
    assert "top_sources" in detail
    assert isinstance(detail["top_sources"], list)


def test_story_detail_unknown_404(client):
    """Unknown story_id returns 404."""
    assert_404(
        client.get("/v1/stories/00000000-0000-0000-0000-00000000dead")
    )


def test_story_articles_paginated(client, seed_articles):
    """GET /v1/stories/{id}/articles returns paginated results."""
    story_ids = {
        a.get("story_id") for a in seed_articles if a.get("story_id")
    }
    assert story_ids, "Need at least one story from seed data"
    story_id = list(story_ids)[0]

    # First page with limit=1
    page1 = assert_json_200(
        client.get(f"/v1/stories/{story_id}/articles?limit=1&offset=0")
    )
    assert "articles" in page1
    assert "total" in page1
    assert isinstance(page1["articles"], list)
    assert len(page1["articles"]) <= 1
    if len(page1["articles"]) == 1:
        art = page1["articles"][0]
        assert "article_id" in art
        assert "headline" in art
        assert "publisher_domain" in art
        assert "published_at" in art

    # Second page (offset=1) if total > 1
    if page1.get("total", 0) > 1:
        page2 = assert_json_200(
            client.get(f"/v1/stories/{story_id}/articles?limit=1&offset=1")
        )
        assert len(page2["articles"]) == 1
        # Should be different article
        if page1["articles"] and page2["articles"]:
            assert (
                page1["articles"][0]["article_id"]
                != page2["articles"][0]["article_id"]
            )


def test_story_articles_unknown_story_404(client):
    """Articles sub-resource on unknown story returns 404."""
    assert_404(
        client.get(
            "/v1/stories/00000000-0000-0000-0000-00000000dead/articles"
        )
    )
