"""GET /v1/feed — ranked story feed."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["feed"])
