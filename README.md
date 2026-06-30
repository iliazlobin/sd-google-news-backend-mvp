# Google News MVP — README

Personalized news aggregation backend. MVP demonstrates ingestion → clustering → ranking → serving.

## Quick start

```bash
# Install
python -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Run (uses SQLite in-memory by default for tests)
.venv/bin/pytest tests/unit/ -v

# Start server
.venv/bin/python -m uvicorn src.google_news.main:app --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/healthz
```

## Docker

```bash
cp .env.example .env
docker compose up -d
docker compose run --rm app alembic upgrade head
curl http://localhost:${APP_PORT:-8010}/healthz
docker compose down
```

## Stack

- Python 3.12, FastAPI, uvicorn
- PostgreSQL 16 (async), Redis 7
- SQLAlchemy 2 (async), Alembic
- scikit-learn (TF-IDF clustering)
- Docker Compose

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| GET | `/v1/feed` | Ranked story feed |
| GET | `/v1/stories/{id}` | Story detail |
| GET | `/v1/stories/{id}/articles` | Paginated articles |
| GET | `/v1/search` | Full-text search |
| POST | `/v1/articles` | Ingest article |
| POST | `/v1/user/preferences` | Update preferences |
| POST | `/v1/events` | Log engagement |
