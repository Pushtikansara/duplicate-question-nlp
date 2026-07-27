from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)

logger = logging.getLogger(__name__)


class PredictAgent(Agent):
    metadata = AgentMetadata(
        agent_id="predict",
        name="Prediction Agent",
        version="1.0",
        description="Makes duplicate question predictions using the ARES inference engine",
        capabilities=frozenset(
            {
                AgentCapability.PREDICTION,
                AgentCapability.SEMANTIC_UNDERSTANDING,
                AgentCapability.MONITORING,
                AgentCapability.INTENT_ANALYSIS,
                AgentCapability.CONFLICT_DETECTION,
            }
        ),
        timeout_seconds=60.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        question1 = input.get("question1", "")
        question2 = input.get("question2", "")
        context = input.get("context", {})
        if not question1:
            question1 = context.get("question1", "")
        if not question2:
            question2 = context.get("question2", "")

        if not question1 or not question2:
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error="Both question1 and question2 are required",
                processing_time_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            from ares._engine import ARES

            engine = ARES()
            model = input.get("model") or context.get("model")
            threshold = input.get("threshold") or context.get("threshold")
            reflect = input.get("reflect", True)

            if model:
                engine = engine.with_model(model)
            if threshold is not None:
                engine = engine.with_threshold(float(threshold) if not isinstance(threshold, float) else threshold)
            if reflect is not None:
                engine = engine.with_reflection(bool(reflect))

            result = engine.predict(question1, question2)
            elapsed = (time.perf_counter() - start) * 1000

            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result={
                    "question1": question1,
                    "question2": question2,
                    "predicted_label": result.predicted_label,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "prob_duplicate": result.prob_duplicate,
                    "prob_non_duplicate": result.prob_non_duplicate,
                    "model_name": result.model_name,
                    "latency_ms": result.latency_ms,
                    "trust_score": result.trust_score,
                    "trust_level": result.trust_level,
                    "risk_level": result.risk_level,
                    "human_review_required": result.human_review_required,
                    "recommendations": result.recommendations,
                    "explanations": result.explanations,
                },
                confidence=result.confidence,
                evidence=[
                    {
                        "type": "prediction",
                        "question1": question1,
                        "question2": question2,
                        "prediction": result.prediction,
                        "confidence": result.confidence,
                    }
                ],
                processing_time_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception("PredictAgent failed")
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error=str(e),
                processing_time_ms=elapsed,
            )
