from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends

from ares.api.dependencies import apply_rate_limit, get_request_id, require_user
from ares.api.models import TraceRequest, TraceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/trace",
    response_model=TraceResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def run_trace(
    req: TraceRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> TraceResponse:
    from ares.orchestration.prediction_service import get_prediction_service

    service = get_prediction_service()
    start = time.time()
    prediction = service.predict_raw(
        req.question1,
        req.question2,
        model=req.model,
        threshold=req.threshold,
    )
    elapsed = (time.time() - start) * 1000
    steps: list[dict[str, Any]] = [
        {"step": "preprocessing", "latency_ms": 0.0},
        {"step": "inference", "latency_ms": prediction.latency_ms},
        {"step": "postprocessing", "latency_ms": 0.0},
    ]
    try:
        from duplicate_question_app._reasoning.reasoning_trace import ReasoningTrace

        rt = ReasoningTrace()
        trace_data = rt.get_trace(req.question1, req.question2) if hasattr(rt, "get_trace") else prediction
    except Exception:
        trace_data = prediction
    return TraceResponse(
        trace=trace_data,
        steps=steps,
        total_latency_ms=elapsed,
        request_id=request_id,
    )
