"""TF-IDF clustering: assign articles to stories by cosine similarity."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from google_news.models.article import Article
from google_news.models.story import Story

SIMILARITY_THRESHOLD = 0.3
CANDIDATE_WINDOW_HOURS = 48


def _build_corpus(articles: list[Article]) -> list[str]:
    """Build text corpus from article headlines + snippets."""
    return [(a.headline or "") + " " + (a.snippet or "") for a in articles]


def _find_best_match(
    new_text: str,
    existing_texts: list[str],
) -> tuple[int, float]:
    """Find the best matching article index and similarity.

    Returns (index, similarity) or (-1, 0.0) if no match.
    """
    if not existing_texts:
        return -1, 0.0

    corpus = existing_texts + [new_text]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf = vectorizer.fit_transform(corpus)

    # Cosine similarity: last row (new) vs all previous rows
    sims = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]

    best_idx = int(sims.argmax())
    best_sim = float(sims[best_idx])

    if best_sim > SIMILARITY_THRESHOLD:
        return best_idx, best_sim
    return -1, 0.0


def _infer_category(headline: str, snippet: str | None) -> str:
    """Infer a simple topic category from headline keywords.

    This is a minimal keyword-based classifier for MVP.
    Real implementation would use a topic model.
    """
    text = ((headline or "") + " " + (snippet or "")).lower()
    # Split into words for word-boundary matching
    words_set = set(text.split())
    keywords: dict[str, set[str]] = {
        "tech": {
            "ai",
            "chip",
            "tech",
            "startup",
            "software",
            "app",
            "nvidia",
            "quantum",
            "silicon",
            "robot",
            "data",
            "cyber",
        },
        "world": {
            "earthquake",
            "war",
            "treaty",
            "diplomat",
            "flood",
            "hurricane",
            "tsunami",
            "quake",
            "refugee",
            "crisis",
            "un",
            "nato",
            "border",
        },
        "sports": {
            "championship",
            "game",
            "cup",
            "final",
            "team",
            "win",
            "goal",
            "touchdown",
            "penalty",
            "playoff",
            "match",
            "score",
            "sports",
            "league",
            "tournament",
        },
        "business": {
            "market",
            "stock",
            "raise",
            "funding",
            "billion",
            "million",
            "acquisition",
            "merger",
            "ipo",
            "revenue",
            "ceo",
            "investor",
            "shares",
            "wall",
            "street",
        },
        "science": {
            "study",
            "research",
            "scientists",
            "discovery",
            "breakthrough",
            "experiment",
            "nasa",
            "space",
            "science",
        },
        "health": {
            "covid",
            "vaccine",
            "hospital",
            "disease",
            "outbreak",
            "medical",
            "drug",
            "fda",
            "health",
            "patient",
        },
    }
    for category, words in keywords.items():
        if words_set & words:
            return category
    return "general"


def _ensure_tz_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC if naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _compute_top_sources(
    articles: list[Article],
    max_sources: int = 5,
) -> list[str]:
    """Compute top N publisher domains by authority score."""
    # Group by domain, keeping highest authority per domain
    best_authority: dict[str, float] = {}
    for a in articles:
        domain = a.publisher_domain
        auth = a.source_authority
        if domain not in best_authority or auth > best_authority[domain]:
            best_authority[domain] = auth

    scored = sorted(best_authority.items(), key=lambda x: x[1], reverse=True)
    return [domain for domain, _ in scored[:max_sources]]


def _best_headline(articles: list[Article]) -> str:
    """Pick the headline from the highest-authority article."""
    best = max(articles, key=lambda a: a.source_authority)
    return best.headline


async def assign_article_to_story(
    db: AsyncSession,
    article: Article,
) -> uuid.UUID:
    """Assign an article to an existing story or create a new one.

    Returns the story_id.
    """
    now = datetime.now(UTC)
    cutoff = datetime.fromtimestamp(now.timestamp() - CANDIDATE_WINDOW_HOURS * 3600, tz=UTC)

    # Fetch recent articles (already assigned to stories)
    stmt = (
        select(Article)
        .where(
            Article.story_id.isnot(None),
            Article.created_at >= cutoff,
        )
        .order_by(Article.created_at.desc())
        .limit(500)
    )
    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    if not candidates:
        return await _create_new_story(db, article)

    # Collect articles by story_id for matching
    story_articles: dict[uuid.UUID, list[Article]] = {}
    for a in candidates:
        story_articles.setdefault(a.story_id, []).append(a)

    # Build a representative text for each story (first article's text)
    story_texts: list[tuple[uuid.UUID, str]] = []
    for sid, arts in story_articles.items():
        rep_text = _build_corpus([arts[0]])[0]
        story_texts.append((sid, rep_text))

    new_text = _build_corpus([article])[0]
    existing_texts = [t for _, t in story_texts]

    best_idx, best_sim = _find_best_match(new_text, existing_texts)

    if best_idx >= 0 and best_sim > SIMILARITY_THRESHOLD:
        best_story_id = story_texts[best_idx][0]
        article.story_id = best_story_id
        await db.flush()
        await _update_story_aggregates(db, best_story_id)
        return best_story_id

    return await _create_new_story(db, article)


async def _create_new_story(
    db: AsyncSession,
    article: Article,
) -> uuid.UUID:
    """Create a new Story from an article and assign the article to it."""
    category = _infer_category(article.headline, article.snippet)
    story = Story(
        canonical_headline=article.headline,
        article_count=1,
        top_sources=[article.publisher_domain],
        category=category,
        first_published_at=article.published_at,
        last_updated_at=datetime.now(UTC),
    )
    db.add(story)
    await db.flush()

    article.story_id = story.story_id
    await db.flush()
    return story.story_id


async def _update_story_aggregates(
    db: AsyncSession,
    story_id: uuid.UUID,
) -> None:
    """Update story aggregates: article_count, top_sources, canonical_headline."""
    # Fetch all articles for this story
    stmt = select(Article).where(Article.story_id == story_id)
    result = await db.execute(stmt)
    articles = list(result.scalars().all())

    if not articles:
        return

    count = len(articles)
    top_sources = _compute_top_sources(articles)
    headline = _best_headline(articles)
    first_pub = min(_ensure_tz_aware(a.published_at) for a in articles)
    last_upd = max(_ensure_tz_aware(a.published_at) for a in articles)

    stmt_upd = (
        update(Story)
        .where(Story.story_id == story_id)
        .values(
            canonical_headline=headline,
            article_count=count,
            top_sources=top_sources,
            first_published_at=first_pub,
            last_updated_at=last_upd,
        )
    )
    await db.execute(stmt_upd)
    await db.flush()
