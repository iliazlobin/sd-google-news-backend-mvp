"""GET /v1/stories/{story_id} + /v1/stories/{story_id}/articles."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["stories"])
