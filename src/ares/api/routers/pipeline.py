from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends

from ares._result import PredictionResult
from ares.api.dependencies import apply_rate_limit, get_request_id, require_user
from ares.api.models import PipelineRequest, PipelineResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/pipeline",
    response_model=PipelineResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def run_pipeline(
    req: PipelineRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> PipelineResponse:
    from ares._engine import ARES

    engine = ARES()
    start = time.time()
    modules_status: dict[str, float] = {}
    executed: list[str] = []
    skipped: list[str] = []
    prediction: PredictionResult | None = None
    error: str | None = None
    try:
        if req.enable_perception:
            t0 = time.time()
            if hasattr(engine, "_perceive"):
                engine._perceive(req.question1, req.question2)
            modules_status["perception"] = (time.time() - t0) * 1000
            executed.append("perception")
        else:
            skipped.append("perception")
    except Exception as e:
        error = str(e)
    if error is None:
        try:
            result = engine.predict(req.question1, req.question2)
            prediction = result
        except Exception as e:
            error = str(e)
    total = (time.time() - start) * 1000
    return PipelineResponse(
        success=error is None,
        question1=req.question1,
        question2=req.question2,
        prediction=prediction.to_dict() if prediction else None,
        modules_executed=executed,
        modules_skipped=skipped,
        total_latency_ms=total,
        module_latencies=modules_status,
        confidence=prediction.confidence if prediction else 0.0,
        error=error,
        request_id=request_id,
    )
