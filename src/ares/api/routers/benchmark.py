from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ares.api.dependencies import get_request_id, require_admin
from ares.api.models import BenchmarkRequest, BenchmarkResult

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/benchmark", dependencies=[Depends(require_admin)])
async def list_benchmarks(
    request_id: str = Depends(get_request_id),
) -> list[dict[str, Any]]:
    try:
        from duplicate_question_app._evaluation.benchmark_runner import BenchmarkRunner

        br = BenchmarkRunner()
        results = br.list_results() if hasattr(br, "list_results") else []
        return results
    except Exception as e:
        logger.warning("Benchmark list failed: %s", e)
        return []


@router.post("/benchmark/run", response_model=BenchmarkResult, dependencies=[Depends(require_admin)])
async def run_benchmark(
    req: BenchmarkRequest,
    request_id: str = Depends(get_request_id),
) -> BenchmarkResult:
    from ares._engine import ARES

    engine = ARES()
    start = time.time()
    metrics: dict[str, float] = {}
    try:
        import time as _time

        import numpy as np

        latencies: list[float] = []
        test_pairs = [
            ("What is Python?", "What is Python programming language?"),
            ("How to learn Java?", "Best way to learn Java programming"),
            ("What is AI?", "What is artificial intelligence?"),
        ]
        for q1, q2 in test_pairs:
            t0 = _time.time()
            if req.model is not None:
                engine = engine.with_model(req.model)
            engine.predict(q1, q2)
            latencies.append((_time.time() - t0) * 1000)
        metrics["avg_latency_ms"] = float(np.mean(latencies))
        metrics["p50_latency_ms"] = float(np.median(latencies))
        metrics["p95_latency_ms"] = float(np.percentile(latencies, 95))
        metrics["p99_latency_ms"] = float(np.percentile(latencies, 99))
        metrics["throughput_qps"] = float(len(latencies) / (sum(latencies) / 1000)) if sum(latencies) > 0 else 0.0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {e}") from e
    total = (time.time() - start) * 1000
    return BenchmarkResult(
        name=req.name or "api-benchmark",
        status="completed",
        metrics=metrics,
        config=req.config,
        model=req.model or "default",
        epochs=req.epochs,
        total_latency_ms=total,
        request_id=request_id,
    )
