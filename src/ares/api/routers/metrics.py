from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from starlette.responses import PlainTextResponse

from ares.api.dependencies import get_request_id, require_admin
from ares.api.metrics import get_metrics_collector as _get_collector
from ares.api.models import MetricsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse, dependencies=[Depends(require_admin)])
async def get_prometheus_metrics() -> str:
    collector = _get_collector()
    raw = collector.get_metrics()
    lines: list[str] = []
    for key, value in raw.items():
        lines.append(f"# HELP {key} ARES metric")
        lines.append(f"# TYPE {key} gauge")
        lines.append(f"{key} {value}")
    return "\n".join(lines) + "\n"


@router.get("/metrics/json", response_model=MetricsResponse, dependencies=[Depends(require_admin)])
async def get_metrics_json(
    request_id: str = Depends(get_request_id),
) -> MetricsResponse:
    collector = _get_collector()
    return MetricsResponse(
        metrics=collector.get_metrics(),
        request_id=request_id,
    )
