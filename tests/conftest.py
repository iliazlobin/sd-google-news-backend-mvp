"""Test fixtures: async HTTP client, test database.

White-box tests use an in-memory SQLite database via pytest fixtures.
Functional tests use the same in-process ASGITransport with DB overridden.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from google_news.database import Base, get_db
from google_news.main import create_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# ── Test database fixtures ────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Session-scoped async SQLite engine (in-memory, shared)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session that rolls back everything at teardown."""
    async with test_engine.connect() as conn:
        async with conn.begin() as trans:
            session_factory = async_sessionmaker(
                bind=conn,
                class_=AsyncSession,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )
            async with session_factory() as session:
                yield session
            await trans.rollback()


# ── HTTP client fixture ───────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(
    test_engine,
    db: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient that talks directly to the FastAPI app (no network).

    Overrides get_db to use the test database session so endpoint handlers
    share the same per-test transaction.
    """
    app = create_app()

    # Capture the session in a closure so the override yields it.
    # Use a list to work around the closure binding issue.
    _session = db

    async def override_get_db():
        yield _session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
