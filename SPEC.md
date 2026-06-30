## 1. Goal & scope

Build an MVP backend that ingests news articles, clusters them into stories, and serves a personalized ranked feed — the core loop of a Google News-style aggregator. The MVP demonstrates the ingestion → clustering → ranking → serving pipeline with a working API, not a mock.

**In scope:**
- Article ingestion via file upload / API (no crawler fleet — seed data for demo)
- Story clustering using text similarity (simplified MinHash or TF-IDF)
- Personalized feed ranking with freshness decay and source authority
- Search across articles/stories with basic filters
- Story detail with source attribution

**Out of scope:**
- Real-time web crawling (seed with static data)
- Push notifications (FCM/APNs)
- Multi-region architecture (single deployment)
- ML-based two-tower ranking (use score-based formula)
- Breaking news detection with cluster momentum
- User authentication (treat user_id as a header)
- WebSub/sitemap integration

## 2. Functional requirements

- **FR-1 — View ranked feed.** `GET /v1/feed?user_id=<id>&limit=30` → returns ranked story clusters with headline, snippet, source count, and thumbnail URL. Ranking blends freshness, source authority, and user topic preferences. Response p95 < 200ms.

- **FR-2 — Browse story coverage.** `GET /v1/stories/{story_id}` → returns canonical headline, top sources, article count. `GET /v1/stories/{story_id}/articles?page_token=&limit=20` → paginated articles sorted by authority DESC then recency DESC.

- **FR-3 — Search articles.** `GET /v1/search?q=<query>&from=<iso>&to=<iso>&limit=20` → full-text search across headlines and snippets, filtered by published_at range. Results grouped by story_id.

- **FR-4 — Manage preferences.** `POST /v1/user/preferences` → set followed_topics and followed_sources. Preferences boost matching stories in the feed.

- **FR-5 — Ingest articles.** `POST /v1/articles` → submit an article (headline, url, snippet, publisher_domain, published_at, language, region). Triggers clustering. Return article_id. Idempotent on url.

- **FR-6 — Log engagement.** `POST /v1/events` → log user interaction (impression, click, dwell). Fire-and-forget, 202 Accepted. Drives ranking personalization.

- **FR-7 — Health check.** `GET /healthz` → 200 OK with service status. Always available.

- **FR-8 — Article dedup.** Duplicate URLs are rejected with 409 Conflict. Near-duplicate detection via text similarity clusters articles into stories.

## 3. Stack & deployment

- **Runtime:** Python 3.12, FastAPI, uvicorn
- **Datastore:** PostgreSQL 16 (articles, stories, users, events), Redis (feed cache)
- **Search:** PostgreSQL full-text search (`tsvector` / `tsquery`) — no Elasticsearch in MVP
- **Clustering:** TF-IDF + cosine similarity (in-process, not distributed)
- **Tests:** pytest + httpx.ASGITransport (in-process), pytest for black-box acceptance
- **Infra:** Docker Compose (app + postgres + redis)
- **Port:** `${APP_PORT:-8010}:8000` (env-overridable, collision-safe)

Design → [System Design: Google News](https://app.notion.com/p/iliazlobin/382d8650-05a8-8190-a73c-e76b51b1061f?p=38fd8650-05a8-8193-bf61-dd6a54468f96&pm=s)
Board → `projects`

## 4. Data model

```
Article
  article_id: UUID (PK)
  url: text (UNIQUE)             ← canonical URL; idempotency key
  publisher_domain: text (INDEX)
  headline: text
  snippet: text
  published_at: timestamptz (INDEX)
  language: text                 ← ISO 639-1
  region: text
  source_authority: float        ← static score 0–1
  story_id: UUID (FK → Story)    ← assigned by clustering
  created_at: timestamptz

Story
  story_id: UUID (PK)
  canonical_headline: text       ← highest-authority article's headline
  article_count: integer
  top_sources: text[]            ← top 5 publisher domains by authority
  category: text                 ← inferred topic label
  first_published_at: timestamptz
  last_updated_at: timestamptz
  created_at: timestamptz

UserProfile
  user_id: UUID (PK)
  followed_topics: text[]        ← explicit topic interests
  followed_sources: text[]       ← explicit publisher preferences
  region: text
  language_prefs: text[]
  created_at: timestamptz

UserEvent
  user_id: UUID (PK)             ← partition key
  event_id: UUID (PK)
  article_id: UUID
  story_id: UUID
  event_type: text               ← impression | click | long_dwell | dismiss
  created_at: timestamptz
```

## 5. API

- `GET /healthz` — health check, 200 OK
- `GET /v1/feed?user_id=<uuid>&limit=30` — ranked feed of story clusters
- `GET /v1/stories/{story_id}` — story detail with canonical headline + top sources
- `GET /v1/stories/{story_id}/articles?limit=20&offset=0` — paginated articles in a story
- `GET /v1/search?q=<query>&from=<iso>&to=<iso>&limit=20` — full-text article search
- `POST /v1/articles` — ingest a new article; triggers clustering
- `POST /v1/user/preferences` — update user topic/source preferences
- `POST /v1/events` — log user engagement event

## 6. Test scenarios

- Feed ranking: freshness decay (older articles score lower), authority boost (high-authority sources rank higher), topic preference boost (followed topics get multiplier)
- Idempotency: duplicate article URL returns 409; duplicate event is accepted (fire-and-forget)
- Search: full-text match on headline, time-range filter, empty results for no match
- Clustering: two articles about same topic with different wording get same story_id
- Pagination: story articles paginate correctly with offset/limit
- Validation: missing required fields → 422; invalid user_id → 404 on feed
- Edge cases: empty feed for new user with no preferences; story with single article

## 7. Module layout

```
sd-google-news-backend-mvp/
├── app/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # pydantic-settings
│   ├── routers/
│   │   ├── feed.py          # GET /v1/feed
│   │   ├── stories.py       # GET /v1/stories/{id}, /articles
│   │   ├── search.py        # GET /v1/search
│   │   ├── articles.py      # POST /v1/articles
│   │   ├── users.py         # POST /v1/user/preferences
│   │   └── events.py        # POST /v1/events
│   ├── services/
│   │   ├── feed_service.py  # ranking logic
│   │   ├── cluster_service.py  # TF-IDF clustering
│   │   ├── search_service.py   # PostgreSQL FTS
│   │   └── event_service.py
│   ├── models/
│   │   ├── article.py       # SQLAlchemy models
│   │   ├── story.py
│   │   ├── user.py
│   │   └── event.py
│   ├── schemas/
│   │   ├── article.py       # Pydantic schemas
│   │   ├── story.py
│   │   ├── feed.py
│   │   └── event.py
│   └── db.py                # async session, engine
├── alembic/                 # migrations
├── tests/
│   ├── unit/                # isolated unit tests
│   ├── functional/          # endpoint scenario tests (in-process)
│   └── conftest.py
├── verify/
│   ├── acceptance/          # black-box e2e contract
│   ├── manifest.env         # UP / READY / ACCEPTANCE / DOWN
│   └── __init__.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── SPEC.md                  # this file
└── README.md
```

## 8. Run

```bash
# Start services
docker compose up --build -d

# Wait for health
curl http://localhost:8010/healthz

# Seed demo data
curl -X POST http://localhost:8010/v1/articles -H "Content-Type: application/json" \
  -d '{"headline":"Breaking: Major earthquake hits Turkey","url":"https://reuters.com/quake-turkey",...}'

# Get feed
curl "http://localhost:8010/v1/feed?user_id=<uuid>"

# Run tests
pytest tests/ verify/acceptance/ -v
```
