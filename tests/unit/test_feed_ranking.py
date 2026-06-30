"""Unit tests for feed ranking formula."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from google_news.services.feed_service import (
    _LAMBDA,
    _authority_multiplier,
    _freshness_decay,
    _topic_boost,
    compute_score,
)


class TestFreshnessDecay:
    """Test e^(-λ × hours_age) decay function."""

    def test_decay_at_zero_hours_is_one(self):
        """Fresh article (age=0) has decay factor 1.0."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        assert _freshness_decay(now, now) == 1.0

    def test_decay_at_six_hours_is_half(self):
        """At 6 hours, decay should be ~0.5 (50% decay target)."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now - timedelta(hours=6)
        result = _freshness_decay(pub, now)
        assert 0.49 < result < 0.51, f"Expected ~0.5, got {result}"

    def test_decay_decreases_with_age(self):
        """Older articles have lower freshness."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        fresh = _freshness_decay(now - timedelta(hours=1), now)
        older = _freshness_decay(now - timedelta(hours=12), now)
        assert fresh > older

    def test_decay_at_48_hours(self):
        """At 48 hours, decay should be small."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now - timedelta(hours=48)
        result = _freshness_decay(pub, now)
        expected = math.exp(-_LAMBDA * 48)
        assert result == expected
        assert result < 0.01  # very stale

    def test_future_article_no_negative_age(self):
        """Article from the future gets decay 1.0 (no negative age)."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now + timedelta(hours=1)
        result = _freshness_decay(pub, now)
        assert result == 1.0


class TestAuthorityMultiplier:
    """Test authority multiplier."""

    def test_low_authority(self):
        assert _authority_multiplier(0.0) == 0.0

    def test_high_authority(self):
        assert _authority_multiplier(1.0) == 1.0

    def test_mid_authority(self):
        assert _authority_multiplier(0.5) == 0.5


class TestTopicBoost:
    """Test 10x topic boost for followed topics."""

    def test_no_followed_topics_returns_one(self):
        assert _topic_boost("tech", []) == 1.0

    def test_empty_category_returns_one(self):
        assert _topic_boost("", ["tech"]) == 1.0

    def test_exact_match_returns_ten(self):
        assert _topic_boost("tech", ["tech"]) == 10.0

    def test_case_insensitive_match(self):
        assert _topic_boost("TECH", ["tech"]) == 10.0
        assert _topic_boost("Tech", ["TECH"]) == 10.0

    def test_no_match_returns_one(self):
        assert _topic_boost("sports", ["tech"]) == 1.0

    def test_partial_match(self):
        """Substring match counts."""
        assert _topic_boost("tech-news", ["tech"]) == 10.0

    def test_multiple_topics(self):
        assert _topic_boost("sports", ["tech", "sports", "world"]) == 10.0


class TestComputeScore:
    """Test composite score computation."""

    def test_fresh_high_authority_matched_topic(self):
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now - timedelta(hours=1)
        score = compute_score(
            published_at=pub,
            source_authority=1.0,
            story_category="tech",
            followed_topics=["tech"],
            now=now,
        )
        # freshness ~ e^(-0.1155*1) ≈ 0.891
        # authority = 1.0
        # topic_boost = 10.0
        # expected ≈ 8.91
        assert 8.0 < score < 10.0, f"Expected ~8.9, got {score}"

    def test_stale_low_authority_no_topic(self):
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now - timedelta(hours=48)
        score = compute_score(
            published_at=pub,
            source_authority=0.2,
            story_category="general",
            followed_topics=["tech"],
            now=now,
        )
        # freshness ≈ e^(-0.1155*48) ≈ 0.0039
        # authority = 0.2
        # topic_boost = 1.0
        # expected ≈ 0.00078
        assert score < 0.01, f"Expected very low, got {score}"

    def test_topic_boost_dominates_authority(self):
        """A matched-topic low-authority article beats unmatched high-authority."""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        pub = now - timedelta(hours=1)

        matched = compute_score(pub, 0.3, "tech", ["tech"], now)
        unmatched = compute_score(pub, 1.0, "sports", ["tech"], now)

        assert matched > unmatched, f"Matched ({matched}) should outrank unmatched ({unmatched})"
