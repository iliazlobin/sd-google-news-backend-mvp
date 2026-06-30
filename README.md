# Google News MVP

[![Lint](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/lint.yml/badge.svg)](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/lint.yml)
[![CI](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/ci.yml)
[![Functional](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/functional.yml/badge.svg)](https://github.com/iliazlobin/sd-google-news-backend-mvp/actions/workflows/functional.yml)

Personalized news aggregation backend — ingests articles, clusters them into stories, and serves a ranked feed.

## Quickstart

```bash
cp .env.example .env
docker compose up -d
```

Wait for services to be healthy, then run migrations and verify:

```bash
docker compose run --rm app alembic upgrade head
curl http://localhost:${APP_PORT:-8010}/healthz
```

Seed a few articles:

```bash
curl -X POST http://localhost:8010/v1/articles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://reuters.com/quake-turkey",
    "headline": "Major earthquake hits Turkey",
    "publisher_domain": "reuters.com",
    "published_at": "2026-06-29T10:00:00Z",
    "snippet": "A 7.8 magnitude earthquake struck southern Turkey...",
    "source_authority": 0.9
  }'

curl -X POST http://localhost:8010/v1/articles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://apnews.com/turkey-quake",
    "headline": "Turkey earthquake: rescue efforts underway",
    "publisher_domain": "apnews.com",
    "published_at": "2026-06-29T11:00:00Z",
    "snippet": "Rescue teams are working through the night after a major earthquake...",
    "source_authority": 0.85
  }'
```

Get the ranked feed:

```bash
curl "http://localhost:8010/v1/feed?user_id=00000000-0000-0000-0000-000000000001"
```

Tear down:

```bash
docker compose down
```

## API Reference

- `GET /healthz` — health check, returns `{"status": "ok", "version": "0.1.0"}`

- `GET /v1/feed?user_id=<uuid>&limit=30` — ranked story feed. Stories are scored by freshness × source authority × topic preference boost. Uncached feed p95 < 200ms.

  ```bash
  curl "http://localhost:8010/v1/feed?user_id=33333333-3333-3333-3333-333333333333&limit=10"
  ```

- `GET /v1/stories/{story_id}` — story detail with canonical headline, top sources, and article count.

  ```bash
  curl "http://localhost:8010/v1/stories/22222222-2222-2222-2222-222222222222"
  ```

- `GET /v1/stories/{story_id}/articles?limit=20&offset=0` — paginated articles within a story, sorted by authority descending then recency.

  ```bash
  curl "http://localhost:8010/v1/stories/22222222-2222-2222-2222-222222222222/articles?limit=5"
  ```

- `GET /v1/search?q=<query>&from=<iso>&to=<iso>&limit=20` — full-text search across headlines and snippets with optional time range.

  ```bash
  curl "http://localhost:8010/v1/search?q=earthquake&from=2026-06-28T00:00:00Z&limit=10"
  ```

- `POST /v1/articles` — ingest a new article and trigger clustering. Returns 201 with `article_id` and `story_id`. Duplicate URLs return 409.

  ```bash
  curl -X POST http://localhost:8010/v1/articles \
    -H "Content-Type: application/json" \
    -d '{"url":"https://example.com/news","headline":"...","publisher_domain":"example.com","published_at":"2026-06-29T12:00:00Z","source_authority":0.5}'
  ```

- `POST /v1/user/preferences` — set followed topics and sources. Upserts user profile.

  ```bash
  curl -X POST http://localhost:8010/v1/user/preferences \
    -H "Content-Type: application/json" \
    -d '{"user_id":"44444444-4444-4444-4444-444444444444","followed_topics":["tech","science"],"followed_sources":["reuters.com"]}'
  ```

- `POST /v1/events` — log engagement event (impression, click, long_dwell, dismiss). Fire-and-forget, returns 202.

  ```bash
  curl -X POST http://localhost:8010/v1/events \
    -H "Content-Type: application/json" \
    -d '{"user_id":"33333333-3333-3333-3333-333333333333","article_id":"...","story_id":"...","event_type":"click"}'
  ```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://google_news:google_news@db:5432/google_news` | PostgreSQL connection (async) |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection for feed cache |
| `HOST` | `0.0.0.0` | uvicorn bind address |
| `APP_PORT` | `8000` | In-container port (host port via `docker-compose.yml`: `${APP_PORT:-8010}`) |
| `LOG_LEVEL` | `info` | Logging verbosity |

Copy `.env.example` to `.env` and adjust as needed. Never commit real secrets — `.env` is gitignored.

## Testing

```bash
# Unit tests (white-box, import app modules)
pytest tests/unit/ -v

# Functional tests (white-box, in-process HTTP)
pytest tests/functional/ -v

# Acceptance tests (black-box, against a running server)
API_BASE_URL=http://localhost:8010 pytest verify/acceptance/ -v

# Everything
pytest tests/ verify/acceptance/ -v
```

## Architecture

A single-service FastAPI monolith backed by PostgreSQL 16 and Redis 7, deployed via Docker Compose.

```
HTTP Client → FastAPI (uvicorn) → PostgreSQL (articles, stories, users, events)
                                 → Redis (feed cache, TTL 60s)
                                 → TF-IDF + Cosine Similarity (in-process clustering)
```

- **Ingestion:** `POST /v1/articles` → check URL uniqueness → insert → TF-IDF cluster assignment
- **Feed:** `GET /v1/feed` → check Redis cache → on miss, compute `freshness × authority × topic_boost` per story → sort → cache
- **Search:** PostgreSQL GIN-indexed `tsvector` on headline + snippet with optional time range filter
- **Clustering:** scikit-learn `TfidfVectorizer` + cosine similarity (threshold 0.35), in-process, no distributed infra

## Limitations

- **No ML ranking.** Uses a score formula (`e^(-λt) × authority_boost × topic_boost`). No two-tower model or learned embeddings.
- **No real crawling.** Articles are ingested via API only. No web crawler, sitemap polling, or RSS feeds.
- **No push notifications.** Feed is pull-only via `GET /v1/feed`.
- **Single-region.** One PostgreSQL instance, one Redis instance. No replication or multi-region routing.
- **No authentication.** User identity is a UUID header. Real auth (JWT/OAuth) is out of MVP scope.
- **In-process clustering.** TF-IDF comparison is O(n²) per batch. Works for MVP volumes (~hundreds of articles per 24h window); needs distributed MinHash/LSH at scale.

## Project Layout

```
.
├── src/google_news/         # Application package
│   ├── main.py              # FastAPI app factory, lifespan
│   ├── config.py            # pydantic-settings
│   ├── database.py          # Async SQLAlchemy engine
│   ├── models/              # SQLAlchemy ORM (Article, Story, UserProfile, UserEvent)
│   ├── schemas/             # Pydantic request/response DTOs
│   ├── routers/             # Thin HTTP handlers
│   └── services/            # Business logic (feed, clustering, search, events)
├── alembic/                 # Database migrations
├── tests/                   # White-box unit & functional tests
├── verify/acceptance/       # Black-box acceptance contract (one file per FR)
├── docker-compose.yml       # App + PostgreSQL + Redis
├── Dockerfile               # Multi-stage Python 3.12-slim
├── pyproject.toml           # Dependencies, pytest, ruff config
├── SPEC.md                  # Full specification & design reference
└── README.md
```
