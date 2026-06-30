"""POST /v1/events — log user engagement."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["events"])
