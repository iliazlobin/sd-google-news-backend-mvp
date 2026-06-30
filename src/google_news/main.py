"""FastAPI application factory with lifespan, CORS, and router mounting."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from google_news.routers import (
    articles_router,
    events_router,
    feed_router,
    health_router,
    search_router,
    stories_router,
    users_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: no special setup needed for MVP."""
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Google News MVP",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(health_router)
    app.include_router(feed_router)
    app.include_router(stories_router)
    app.include_router(search_router)
    app.include_router(articles_router)
    app.include_router(users_router)
    app.include_router(events_router)

    return app


app = create_app()
