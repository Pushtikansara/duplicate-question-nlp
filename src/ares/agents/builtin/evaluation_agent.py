from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput


class EvaluationAgent(Agent):
    metadata = AgentMetadata(
        agent_id="evaluation",
        name="Evaluation Agent",
        version="1.0",
        description="Evaluates prediction quality, tracks metrics, and identifies failure modes",
        capabilities=frozenset({AgentCapability.MONITORING, AgentCapability.CONFIDENCE_ASSESSMENT}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        prediction = input.get("prediction", {})
        semantic = input.get("semantic_validation", {})
        reflection = input.get("reflection", {})

        metrics = {
            "confidence": prediction.get("confidence", 0),
            "latency_ms": prediction.get("latency_ms", 0),
            "has_ambiguity": semantic.get("ambiguity_detected", False) if semantic else False,
            "trust_score": reflection.get("trust_score", 0) if reflection else 0,
            "needs_review": reflection.get("human_review_required", False) if reflection else False,
        }

        quality = (
            "high"
            if metrics["confidence"] >= 0.8 and metrics["trust_score"] >= 0.7 and not metrics["needs_review"]
            else "medium"
            if metrics["confidence"] >= 0.5
            else "low"
        )
        metrics["quality"] = quality

        elapsed = (time.perf_counter() - start) * 1000
        return self.create_output(
            status=AgentExecutionStatus.SUCCESS,
            result=metrics,
            confidence=metrics["confidence"],
            processing_time_ms=elapsed,
        )
