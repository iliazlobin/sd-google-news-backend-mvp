# Build: docker build -t google-news .
# Run:   docker compose up -d

# ============================================================================
# Stage 1: Build
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml pyproject.toml
RUN pip install --no-cache-dir --target=/build/deps \
    fastapi uvicorn sqlalchemy asyncpg alembic \
    pydantic-settings redis httpx scikit-learn

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Copy deps from builder
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages
# Console-script shims (uvicorn, alembic, ...) land in deps/bin under --target
COPY --from=builder /build/deps/bin /usr/local/bin

# Copy application source
COPY alembic.ini alembic.ini
COPY alembic/ alembic/
COPY src/ src/
COPY pyproject.toml pyproject.toml

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

CMD ["python", "-m", "uvicorn", "src.google_news.main:app", "--host", "0.0.0.0", "--port", "8000"]
