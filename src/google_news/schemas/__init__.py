"""Pydantic request/response schemas for Google News MVP."""

from google_news.schemas.article import ArticleCreate, ArticleResponse
from google_news.schemas.story import StoryDetailResponse, StoryArticlesResponse
from google_news.schemas.feed import FeedResponse, FeedStory
from google_news.schemas.user import PreferencesUpdate, PreferencesResponse
from google_news.schemas.event import EventCreate, EventResponse
from google_news.schemas.search import SearchResponse, SearchResult

__all__ = [
    "ArticleCreate", "ArticleResponse",
    "StoryDetailResponse", "StoryArticlesResponse",
    "FeedResponse", "FeedStory",
    "PreferencesUpdate", "PreferencesResponse",
    "EventCreate", "EventResponse",
    "SearchResponse", "SearchResult",
]
