"""FR-5: POST /v1/articles ingests article, triggers clustering;
duplicate URL → 409.

AC-5: Ingest new article → 201 with article_id + story_id.
Duplicate URL → 409. Missing required fields → 422.
"""

import uuid

from verify.acceptance.conftest import assert_201, assert_409, assert_422, assert_json_200


def test_ingest_article_success(client):
    """Ingest a new article returns 201 with article_id and story_id."""
    unique_url = f"https://test-news.com/unique-article-{uuid.uuid4()}.html"

    article = {
        "url": unique_url,
        "headline": "Test: new scientific breakthrough announced",
        "snippet": "Scientists have announced a major breakthrough in quantum computing that could revolutionize the field.",
        "publisher_domain": "test-news.com",
        "published_at": "2026-06-29T10:00:00Z",
        "language": "en",
        "region": "world",
        "source_authority": 0.70,
    }

    resp = assert_201(client.post("/v1/articles", json=article))

    assert "article_id" in resp
    assert "story_id" in resp
    assert resp["url"] == unique_url  # or at least the URL is echoed

    # Verify article_id is a valid UUID
    uuid.UUID(resp["article_id"])
    uuid.UUID(resp["story_id"])


def test_ingest_article_duplicate_url_409(client):
    """Ingesting an article with an existing URL returns 409."""
    dup_url = f"https://dup-test.com/duplicate-article-{uuid.uuid4()}.html"

    article = {
        "url": dup_url,
        "headline": "Duplicate article test",
        "snippet": "This is a test of duplicate detection.",
        "publisher_domain": "dup-test.com",
        "published_at": "2026-06-29T10:00:00Z",
        "language": "en",
        "region": "test",
        "source_authority": 0.50,
    }

    # First ingest succeeds
    first = assert_201(client.post("/v1/articles", json=article))
    assert "article_id" in first

    # Second ingest with same URL → 409
    err = assert_409(client.post("/v1/articles", json=article))
    assert "detail" in err or "existing_article_id" in err


def test_ingest_article_missing_required_fields_422(client):
    """Missing required fields returns 422."""
    # Missing headline
    assert_422(
        client.post(
            "/v1/articles",
            json={
                "url": f"https://bad.com/article-{uuid.uuid4()}.html",
                "publisher_domain": "bad.com",
                "published_at": "2026-06-29T10:00:00Z",
            },
        )
    )

    # Missing url
    assert_422(
        client.post(
            "/v1/articles",
            json={
                "headline": "No URL article",
                "publisher_domain": "bad.com",
                "published_at": "2026-06-29T10:00:00Z",
            },
        )
    )


def test_ingest_article_minimal_fields(client):
    """Ingest with only required fields (headline, url, publisher_domain, published_at)."""
    url = f"https://minimal-news.com/minimal-{uuid.uuid4()}.html"
    article = {
        "url": url,
        "headline": "Minimal article for testing",
        "publisher_domain": "minimal-news.com",
        "published_at": "2026-06-29T10:00:00Z",
    }

    resp = assert_201(client.post("/v1/articles", json=article))
    assert "article_id" in resp
    assert "story_id" in resp
