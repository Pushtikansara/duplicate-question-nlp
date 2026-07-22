from __future__ import annotations

import logging
import platform
import sys
import time

from fastapi import APIRouter, Depends

from ares.api.dependencies import get_request_id
from ares.api.models import VersionResponse
from ares.api.version import API_VERSION, ARES_VERSION

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


@router.get("/version", response_model=VersionResponse)
async def get_version(request_id: str = Depends(get_request_id)) -> VersionResponse:
    return VersionResponse(
        version=ARES_VERSION,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        api_version=API_VERSION,
        build=None,
        request_id=request_id,
    )
