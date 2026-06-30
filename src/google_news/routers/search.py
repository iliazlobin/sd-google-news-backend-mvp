"""GET /v1/search — full-text article search."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["search"])
