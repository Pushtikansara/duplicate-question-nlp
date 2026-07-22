from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends

from ares.api.dependencies import apply_rate_limit, get_request_id, require_user
from ares.api.models import ReflectionRequest, ReflectionResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/reflection",
    response_model=ReflectionResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def run_reflection(
    req: ReflectionRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ReflectionResponse:
    from ares._engine import ARES
    from ares._result import PredictionResult

    engine = ARES()
    start = time.time()
    prediction: PredictionResult | None = None
    if req.prediction is not None:
        prediction = engine.predict(req.question1, req.question2)
    else:
        prediction = engine.predict(req.question1, req.question2)
    result: dict[str, Any] = (
        engine.reflect(req.question1, req.question2, prediction) if hasattr(engine, "reflect") else {}
    )
    elapsed = (time.time() - start) * 1000
    trust_score = result.get("trust_score", prediction.trust_score if prediction else 0.0)
    trust_level = result.get("trust_level", prediction.trust_level if prediction else "unknown")
    risk_level = result.get("risk_level", prediction.risk_level if prediction else "unknown")
    return ReflectionResponse(
        trust_score=trust_score,
        trust_level=trust_level,
        risk_level=risk_level,
        confidence=result.get("confidence", prediction.confidence if prediction else 0.0),
        explanation=result.get("explanation", ""),
        confidence_audit=result.get("confidence_audit"),
        consistency_check=result.get("consistency_check"),
        evidence=result.get("evidence", []),
        recommendations=result.get("recommendations", []),
        latency_ms=elapsed,
        request_id=request_id,
    )
