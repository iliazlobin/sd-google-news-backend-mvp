"""POST /v1/articles — ingest article."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["articles"])
