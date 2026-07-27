from __future__ import annotations

import logging
import time
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__name__)


def stream_predictions(
    pairs: list[tuple[str, str]],
    model: str = "",
    threshold: float = 0.5,
) -> Generator[dict[str, Any]]:
    from ares._engine import ARES

    engine = ARES()
    yield {"event": "start", "total": len(pairs)}
    for i, (q1, q2) in enumerate(pairs):
        try:
            t0 = time.time()
            result = engine.predict(q1, q2)
            elapsed = (time.time() - t0) * 1000
            yield {
                "event": "result",
                "index": i,
                "question1": q1,
                "question2": q2,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "latency_ms": round(elapsed, 2),
            }
        except Exception as e:
            yield {"event": "error", "index": i, "error": str(e)}
    yield {"event": "done", "total": len(pairs)}
