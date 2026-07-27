from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ares._result import PredictionResult
from ares.api.dependencies import apply_rate_limit, get_request_id, require_user
from ares.api.models import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from ares.api.streaming import event_stream, stream_predictions
from ares.api.validators import validate_model_name, validate_question_pair, validate_threshold

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_prediction(
    question1: str,
    question2: str,
    model: str | None = None,
    threshold: float | None = None,
    reflect: bool | None = None,
) -> PredictionResult:
    from ares import ARES

    engine = ARES()
    model_name = validate_model_name(model)
    thresh = validate_threshold(threshold)
    if model_name is not None:
        engine = engine.with_model(model_name)
    if thresh is not None:
        engine = engine.with_threshold(thresh)
    if reflect is not None:
        engine = engine.with_reflection(reflect)
    result = engine.predict(question1, question2)
    return result


@router.post(
    "/predict",
    response_model=PredictionResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def predict(
    req: PredictionRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> PredictionResponse:
    validate_question_pair(req.question1, req.question2)
    try:
        result = _run_prediction(req.question1, req.question2, req.model, req.threshold, req.reflect)
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return PredictionResponse(
        question1=req.question1,
        question2=req.question2,
        predicted_label=result.predicted_label,
        prediction=result.prediction,
        prob_duplicate=result.prob_duplicate,
        prob_non_duplicate=result.prob_non_duplicate,
        confidence=result.confidence,
        threshold=req.threshold or 0.5,
        model_label=result.model_name,
        latency_ms=result.latency_ms,
        trust_score=result.trust_score,
        trust_level=result.trust_level,
        risk_level=result.risk_level,
        request_id=request_id,
    )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    dependencies=[Depends(apply_rate_limit)],
)
async def predict_batch(
    req: BatchPredictionRequest,
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> BatchPredictionResponse:
    start = time.time()
    results: list[PredictionResponse] = []
    successes = 0
    failures = 0
    for q1, q2 in req.pairs:
        try:
            validate_question_pair(q1, q2)
            result = _run_prediction(q1, q2, req.model, req.threshold, req.reflect)
            results.append(
                PredictionResponse(
                    question1=q1,
                    question2=q2,
                    predicted_label=result.predicted_label,
                    prediction=result.prediction,
                    prob_duplicate=result.prob_duplicate,
                    prob_non_duplicate=result.prob_non_duplicate,
                    confidence=result.confidence,
                    threshold=req.threshold or 0.5,
                    model_label=result.model_name,
                    latency_ms=result.latency_ms,
                    request_id=request_id,
                )
            )
            successes += 1
        except Exception as e:
            failures += 1
            logger.warning("Batch item failed: %s", e)
    total = (time.time() - start) * 1000
    return BatchPredictionResponse(
        results=results,
        total_latency_ms=total,
        average_latency_ms=total / max(len(req.pairs), 1),
        success_count=successes,
        failure_count=failures,
        request_id=request_id,
    )


@router.post(
    "/predict/stream",
    dependencies=[Depends(apply_rate_limit)],
)
async def predict_stream(
    req: BatchPredictionRequest,
    token: dict[str, Any] = Depends(require_user),
) -> StreamingResponse:
    model = req.model or ""
    return await event_stream(
        stream_predictions(
            req.pairs,
            model,
            req.threshold or 0.5,
        )
    )


@router.post(
    "/predict/upload",
    dependencies=[Depends(apply_rate_limit)],
)
async def predict_upload(
    file: UploadFile = File(...),
    token: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> BatchPredictionResponse:
    from ares.api.uploads import get_upload_manager

    content = await file.read()
    filepath = await get_upload_manager().save_upload(file.filename or "upload.csv", content)
    import pandas as pd

    try:
        df = pd.read_csv(filepath)
        q1_col = df.iloc[:, 0].astype(str)
        q2_col = df.iloc[:, 1].astype(str)
        pairs: list[tuple[str, str]] = list(zip(q1_col, q2_col, strict=True))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse upload: {e}") from e
    batch_result: BatchPredictionResponse = await predict_batch(
        BatchPredictionRequest(pairs=pairs),
        token=token,
        request_id=request_id,
    )
    return batch_result
