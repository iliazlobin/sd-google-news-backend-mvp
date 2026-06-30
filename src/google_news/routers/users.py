"""POST /v1/user/preferences — update user preferences."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["users"])
