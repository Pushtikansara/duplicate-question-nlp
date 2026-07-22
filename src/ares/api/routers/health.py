from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from ares.api.dependencies import get_request_id
from ares.api.health import build_health_response
from ares.api.models import HealthResponse
from ares.api.version import ARES_VERSION

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request_id: str = Depends(get_request_id)) -> HealthResponse:
    return build_health_response(ARES_VERSION, request_id)
