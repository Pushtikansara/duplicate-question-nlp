from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class StreamEvent:
    def __init__(self, event: str, data: Any) -> None:
        self.event = event
        self.data = data

    def format(self) -> str:
        lines = [f"event: {self.event}"]
        payload = json.dumps(self.data, default=str)
        lines.extend(f"data: {line}" for line in payload.split("\n"))
        lines.append("")
        return "\n".join(lines)


async def event_stream(
    generator: AsyncGenerator[StreamEvent],
) -> StreamingResponse:
    async def _generate() -> AsyncGenerator[bytes]:
        async for event in generator:
            yield event.format().encode("utf-8")
            yield b"\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def stream_predictions(
    question_pairs: list[tuple[str, str]],
    model: str,
    threshold: float,
) -> AsyncGenerator[StreamEvent]:
    from ares import ARES

    engine = ARES().with_model(model).with_threshold(threshold)
    yield StreamEvent("start", {"total": len(question_pairs), "model": model})

    for i, (q1, q2) in enumerate(question_pairs):
        start = time.time()
        try:
            result = engine.predict(q1, q2)
            elapsed = (time.time() - start) * 1000
            yield StreamEvent(
                "result",
                {
                    "index": i,
                    "question1": q1,
                    "question2": q2,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "latency_ms": round(elapsed, 2),
                },
            )
        except Exception as e:
            yield StreamEvent(
                "error",
                {
                    "index": i,
                    "question1": q1,
                    "question2": q2,
                    "error": str(e),
                },
            )

    yield StreamEvent("done", {"total": len(question_pairs)})
