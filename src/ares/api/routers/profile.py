from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ares.api.dependencies import get_request_id, require_admin
from ares.api.models import ProfileRequest, ProfileResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/profile", response_model=ProfileResponse, dependencies=[Depends(require_admin)])
async def run_profile(
    req: ProfileRequest,
    request_id: str = Depends(get_request_id),
) -> ProfileResponse:
    from ares._engine import ARES

    engine = ARES()
    start = time.time()
    profiled_functions: list[dict[str, Any]] = []
    try:
        from duplicate_question_app._profiling import Profiler

        profiler = Profiler()
        profiler.enable()
        test_pairs = [
            ("What is Python?", "What is Python programming?"),
            ("How to code?", "How to write code?"),
        ]
        for q1, q2 in test_pairs:
            engine.predict(q1, q2)
        profiler.disable()
        stats = profiler.get_stats()
        for func_name, entry in stats.items():
            profiled_functions.append(
                {
                    "name": func_name,
                    "total_time_ms": getattr(entry, "total_time_ms", 0.0),
                    "call_count": getattr(entry, "call_count", 0),
                    "avg_time_ms": getattr(entry, "avg_time_ms", 0.0),
                    "min_time_ms": getattr(entry, "min_time_ms", 0.0),
                    "max_time_ms": getattr(entry, "max_time_ms", 0.0),
                }
            )
    except Exception as e:
        logger.warning("Profiling failed: %s", e)
    total = (time.time() - start) * 1000
    return ProfileResponse(
        profile={"mode": "api", "duration_seconds": req.duration_seconds},
        functions=profiled_functions,
        total_time_ms=total,
        request_id=request_id,
    )


@router.get("/profile/metrics", dependencies=[Depends(require_admin)])
async def get_profile_metrics(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    try:
        from duplicate_question_app._profiling import Profiler

        profiler = Profiler()
        stats = profiler.get_stats()
        return {
            "functions": len(stats),
            "stats": {k: str(v) for k, v in stats.items()},
            "request_id": request_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
