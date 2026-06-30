"""Unit tests for TF-IDF clustering similarity."""

from __future__ import annotations

from google_news.models.article import Article
from google_news.services.cluster_service import (
    SIMILARITY_THRESHOLD,
    _best_headline,
    _build_corpus,
    _compute_top_sources,
    _find_best_match,
    _infer_category,
)


class TestBuildCorpus:
    def test_headline_only(self):
        articles = [
            Article(headline="Breaking news", snippet=None),
        ]
        corpus = _build_corpus(articles)
        assert corpus == ["Breaking news "]

    def test_headline_and_snippet(self):
        articles = [
            Article(headline="Title", snippet="Some text here"),
        ]
        corpus = _build_corpus(articles)
        assert corpus == ["Title Some text here"]


class TestFindBestMatch:
    def test_empty_existing_returns_no_match(self):
        idx, sim = _find_best_match("new article text", [])
        assert idx == -1
        assert sim == 0.0

    def test_identical_texts_match(self):
        text = "Earthquake strikes coastal region causing tsunami warning"
        idx, sim = _find_best_match(text, [text])
        assert idx == 0
        assert sim > 0.9, f"Expected high similarity, got {sim}"

    def test_similar_texts_match(self):
        existing = [
            "Powerful 6.8 magnitude earthquake struck the coastal region today "
            "causing widespread damage and triggering tsunami warnings",
            "AI startup raises 500 million in funding round for new chip design",
        ]
        new = (
            "Authorities issued a tsunami warning following a 6.8 magnitude "
            "earthquake that struck the coastal region with reports of damage"
        )
        idx, sim = _find_best_match(new, existing)
        assert idx == 0  # should match the earthquake article
        assert sim > SIMILARITY_THRESHOLD, f"Expected >{SIMILARITY_THRESHOLD}, got {sim}"

    def test_dissimilar_texts_dont_match(self):
        existing = [
            "Major earthquake hits Turkey, thousands displaced",
        ]
        new = "New AI chip design promises 10x performance improvement"
        idx, sim = _find_best_match(new, existing)
        # Should either be no match or very low similarity
        if idx >= 0:
            assert sim <= SIMILARITY_THRESHOLD, f"Dissimilar texts should not match, but got {sim}"

    def test_single_existing_unrelated(self):
        existing = ["World Cup final ends in penalty shootout"]
        new = "Scientists discover new quantum computing breakthrough"
        idx, sim = _find_best_match(new, existing)
        if idx >= 0:
            assert sim <= SIMILARITY_THRESHOLD, f"Unrelated texts should not cluster, got {sim}"


class TestInferCategory:
    def test_tech_category(self):
        cat = _infer_category("AI chip startup raises $500M", "The AI hardware space is heating up")
        assert cat == "tech"

    def test_world_category(self):
        cat = _infer_category("Major earthquake hits coastal region", None)
        assert cat == "world"

    def test_sports_category(self):
        cat = _infer_category("Championship game ends in stunning upset", None)
        assert cat == "sports"

    def test_business_category(self):
        cat = _infer_category("Stock market hits all-time high as investors rally", None)
        assert cat == "business"

    def test_unknown_falls_to_general(self):
        cat = _infer_category("Local town holds annual parade", None)
        assert cat == "general"


class TestComputeTopSources:
    def test_empty_returns_empty(self):
        assert _compute_top_sources([]) == []

    def test_sorts_by_authority(self):
        articles = [
            Article(publisher_domain="low.com", source_authority=0.3, headline="a"),
            Article(publisher_domain="high.com", source_authority=0.9, headline="b"),
            Article(publisher_domain="mid.com", source_authority=0.6, headline="c"),
        ]
        sources = _compute_top_sources(articles, max_sources=2)
        assert sources == ["high.com", "mid.com"]

    def test_deduplicates_domains(self):
        articles = [
            Article(publisher_domain="same.com", source_authority=0.9, headline="a"),
            Article(publisher_domain="same.com", source_authority=0.8, headline="b"),
        ]
        sources = _compute_top_sources(articles)
        assert sources == ["same.com"]

    def test_respects_max_sources(self):
        articles = [
            Article(publisher_domain=f"src{i}.com", source_authority=0.9 - i * 0.1, headline="x")
            for i in range(10)
        ]
        sources = _compute_top_sources(articles, max_sources=3)
        assert len(sources) == 3


class TestBestHeadline:
    def test_picks_highest_authority(self):
        articles = [
            Article(headline="Low auth headline", source_authority=0.3, publisher_domain="a.com"),
            Article(headline="High auth headline", source_authority=0.9, publisher_domain="b.com"),
        ]
        assert _best_headline(articles) == "High auth headline"

    def test_single_article(self):
        articles = [
            Article(headline="Only headline", source_authority=0.5, publisher_domain="a.com"),
        ]
        assert _best_headline(articles) == "Only headline"
