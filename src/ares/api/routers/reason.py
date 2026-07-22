from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends

from ares.api.dependencies import apply_rate_limit, get_request_id, require_user
from ares.api.models import ReasonRequest, ReasonResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/reason",
    response_model=ReasonResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def reason(
    req: ReasonRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ReasonResponse:
    from ares._engine import ARES

    engine = ARES()
    start = time.time()
    if req.model is not None:
        engine = engine.with_model(req.model)
    if req.threshold is not None:
        engine = engine.with_threshold(req.threshold)
    prediction = engine.predict(req.question1, req.question2)
    elapsed = (time.time() - start) * 1000
    trace: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    try:
        from duplicate_question_app._reasoning.reasoning_engine import ReasoningEngine

        re_engine = ReasoningEngine()
        trace = re_engine.get_trace() if hasattr(re_engine, "get_trace") else []
    except Exception:
        trace = [
            {
                "step": "prediction",
                "model": req.model or "default",
                "latency_ms": round(elapsed, 2),
            }
        ]
    return ReasonResponse(
        question1=req.question1,
        question2=req.question2,
        prediction=prediction.to_dict(),
        reasoning_trace=trace,
        evidence=evidence,
        confidence=prediction.confidence,
        latency_ms=elapsed,
        request_id=request_id,
    )
