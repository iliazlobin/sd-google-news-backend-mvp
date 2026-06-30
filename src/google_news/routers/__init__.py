"""API routers for Google News MVP."""

from google_news.routers.health import router as health_router
from google_news.routers.feed import router as feed_router
from google_news.routers.stories import router as stories_router
from google_news.routers.search import router as search_router
from google_news.routers.articles import router as articles_router
from google_news.routers.users import router as users_router
from google_news.routers.events import router as events_router

__all__ = [
    "health_router",
    "feed_router",
    "stories_router",
    "search_router",
    "articles_router",
    "users_router",
    "events_router",
]
