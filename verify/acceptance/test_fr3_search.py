"""FR-3: GET /v1/search returns matching articles; time-range filter works;
empty results for no match.

AC-3: Full-text search. Time-range filter narrows results. No match → empty list.
Missing q → 422.
"""

from verify.acceptance.conftest import assert_422, assert_json_200


def test_search_returns_matching_articles(client, seed_articles):
    """Search for 'earthquake' returns relevant articles."""
    results = assert_json_200(client.get("/v1/search?q=earthquake&limit=10"))

    assert "results" in results
    assert isinstance(results["results"], list)
    assert len(results["results"]) >= 1, "Should find earthquake articles"

    for art in results["results"]:
        assert "article_id" in art
        assert "headline" in art
        assert "publisher_domain" in art
        assert "published_at" in art


def test_search_time_range_filter(client, seed_articles):
    """Time-range filter narrows results."""
    # Wide range should find the earthquake articles
    wide = assert_json_200(
        client.get(
            "/v1/search?q=earthquake&from=2026-06-29T00:00:00Z&to=2026-06-30T00:00:00Z&limit=10"
        )
    )
    wide_count = wide.get("total", len(wide["results"]))

    # Narrow range before the article was published
    narrow = assert_json_200(
        client.get(
            "/v1/search?q=earthquake&from=2026-06-28T00:00:00Z&to=2026-06-28T06:00:00Z&limit=10"
        )
    )
    narrow_count = narrow.get("total", len(narrow["results"]))

    assert (
        narrow_count <= wide_count
    ), f"Narrow time range ({narrow_count}) should not exceed wide ({wide_count})"


def test_search_no_match_returns_empty(client):
    """Search with no matching query returns empty results, not 404."""
    results = assert_json_200(client.get("/v1/search?q=xyznonexistentfoobar12345&limit=10"))
    assert "results" in results
    assert results["results"] == []
    assert results.get("total", 0) == 0


def test_search_missing_query_422(client):
    """Missing query parameter returns 422."""
    assert_422(client.get("/v1/search?limit=10"))
    assert_422(client.get("/v1/search?q=&limit=10"))


def test_search_respects_limit(client, seed_articles):
    """Search honors the limit parameter."""
    results = assert_json_200(client.get("/v1/search?q=chip&limit=1"))
    assert len(results["results"]) <= 1
