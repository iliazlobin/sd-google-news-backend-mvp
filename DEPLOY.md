# Google News MVP — Deploy Guide

Stack: FastAPI (Python 3.12) + PostgreSQL 16 + Redis 7, orchestrated with Docker Compose.

## Prerequisites

- Docker Engine 24+ with Compose plugin (`docker compose`, not `docker-compose`)
- Git

## Quick Start

```bash
git clone <repo-url> && cd sd-google-news-backend-mvp

cp .env.example .env

docker compose up --build -d

docker compose exec app alembic upgrade head

curl http://localhost:${APP_PORT:-8010}/healthz
```

Seed example:

```bash
curl -X POST http://localhost:${APP_PORT:-8010}/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"url":"https://reuters.com/quake","headline":"Earthquake","snippet":"...","publisher_domain":"reuters.com","published_at":"2026-06-29T06:00:00Z","language":"en","region":"world","source_authority":0.95}'
```

## Health Checks

- App: `curl http://localhost:8010/healthz` → `{"status":"ok"}`
- Postgres: `docker compose exec db pg_isready -U google_news` → `accepting connections`
- Redis: `docker compose exec redis redis-cli ping` → `PONG`

All three services use compose healthchecks with `depends_on` and `condition: service_healthy`.

## Ports

- App: container 8000, host `${APP_PORT:-8010}` (the only service exposed)
- Postgres: container 5432, no host port (internal compose network)
- Redis: container 6379, no host port (internal compose network)

Override `APP_PORT` in `.env` if 8010 is taken.

## Environment Variables

See `.env.example` for the full list. Key variables:

- `DATABASE_URL` — PostgreSQL connection (asyncpg driver)
- `REDIS_URL` — Redis connection
- `SECRET_KEY` — reserved for future auth (not yet used by MVP)
- `APP_PORT` — host port for the app service (default 8010)
- `HOST` — FastAPI bind address (default 0.0.0.0)
- `LOG_LEVEL` — logging verbosity (default info)

## Running Tests

### Unit tests
```bash
pip install -e ".[dev]"
pytest tests/unit/ -v
```

### Functional tests (in-process, no Docker needed)
```bash
DATABASE_URL=postgresql+asyncpg://google_news:google_news@localhost:5432/google_news \
REDIS_URL=redis://localhost:6379/0 \
pytest tests/functional/ -v
```

### Acceptance tests (black-box, requires running app)
```bash
API_BASE_URL=http://localhost:8010 pytest verify/acceptance/ -v
```

## Migrations

```bash
docker compose exec app alembic upgrade head
```

Create new revisions:

```bash
docker compose exec app alembic revision --autogenerate -m "description"
```

## Teardown

```bash
docker compose down       # stop containers, keep volumes
docker compose down -v    # stop + remove volumes (clean state)
```

## GitHub Copilot Code Review

(Manual setup — advisory, not a merge gate.)

1. Go to repo Settings → Code security → GitHub Copilot → Code review
2. Enable "Copilot code review" (advisory mode)
3. Optionally enable for all pull requests

## CI/CD

GitHub Actions workflows (`.github/workflows/`):

- **lint.yml** — ruff check + format check (v0.8.0). Triggers on push, PR, daily.
- **ci.yml** — unit tests + docker compose e2e (sources verify/manifest.env). Triggers on push, PR, daily.
- **functional.yml** — functional tests against live Postgres service. Triggers on push, PR, daily.

All workflows use `permissions: contents: read` and per-ref concurrency groups.

## Troubleshooting

**App won't start:** `docker compose logs app`. Common causes: Postgres not healthy yet, port collision.

**Health check fails:**
```bash
docker compose exec app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/healthz').read())"
```

**Migrations fail (clean restart):**
```bash
docker compose down -v && docker compose up --build -d && docker compose exec app alembic upgrade head
```
