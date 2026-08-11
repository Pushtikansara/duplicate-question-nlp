from __future__ import annotations

import logging
import time
from typing import Any, cast

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
    from ares._result import PredictionResult
    from ares.orchestration.prediction_service import get_prediction_service

    service = get_prediction_service()
    start = time.time()
    prediction_result = service.predict_raw(
        req.question1,
        req.question2,
    )
    prediction = cast(PredictionResult, prediction_result)
    elapsed = (time.time() - start) * 1000
    evidence_raw = getattr(prediction, "explanations", None) or []
    evidence = [] if isinstance(evidence_raw, dict) else list(evidence_raw)
    recommendations_raw = getattr(prediction, "recommendations", None) or []
    recommendations = [] if not isinstance(recommendations_raw, list) else recommendations_raw
    return ReflectionResponse(
        trust_score=prediction.trust_score,
        trust_level=prediction.trust_level,
        risk_level=prediction.risk_level,
        confidence=prediction.confidence,
        explanation="",
        confidence_audit=None,
        consistency_check=None,
        evidence=evidence,
        recommendations=recommendations,
        latency_ms=elapsed,
        request_id=request_id,
    )
