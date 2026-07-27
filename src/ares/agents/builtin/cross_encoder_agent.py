from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput
from ares.inference.dispatcher import InferenceDispatcher


class CrossEncoderAgent(Agent):
    metadata = AgentMetadata(
        agent_id="cross_encoder",
        name="Cross-Encoder Agent",
        version="1.0",
        description="Runs cross-encoder models for joint question pair encoding and scoring",
        capabilities=frozenset({AgentCapability.PREDICTION, AgentCapability.SEMANTIC_UNDERSTANDING}),
        timeout_seconds=60.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        q1 = input.get("question1", "") or input.get("context", {}).get("question1", "")
        q2 = input.get("question2", "") or input.get("context", {}).get("question2", "")
        if not q1 or not q2:
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error="Both questions required",
                processing_time_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            result = InferenceDispatcher.predict("DeBERTa-v3 Cross-Encoder", q1, q2)
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result={
                    "predicted_label": result.predicted_label,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "prob_duplicate": result.prob_duplicate,
                    "model_name": result.model_name,
                    "latency_ms": result.latency_ms,
                    "raw_logits": result.raw_logits,
                    "softmax": result.softmax,
                },
                confidence=result.confidence,
                processing_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(status=AgentExecutionStatus.FAILURE, error=str(e), processing_time_ms=elapsed)
