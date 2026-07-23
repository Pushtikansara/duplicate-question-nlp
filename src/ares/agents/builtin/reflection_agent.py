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


class ReflectionAgent(Agent):
    metadata = AgentMetadata(
        agent_id="reflection",
        name="Reflection Agent",
        version="1.0",
        description="Performs reflection on predictions to assess trust, risk, and confidence",
        capabilities=frozenset({AgentCapability.REFLECTION, AgentCapability.CONFIDENCE_ASSESSMENT}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        prediction = input.get("prediction", input.get("result", {}))
        question1 = input.get("question1", "")
        question2 = input.get("question2", "")

        if isinstance(prediction, dict) and not prediction:
            prediction = {
                "predicted_label": input.get("predicted_label", 0),
                "prediction": input.get("prediction", "unknown"),
                "confidence": input.get("confidence", 0.0),
                "prob_duplicate": input.get("prob_duplicate", 0.0),
                "prob_non_duplicate": input.get("prob_non_duplicate", 0.0),
            }

        try:
            from duplicate_question_app._reflection.reflection_engine import ReflectionEngine

            engine = ReflectionEngine()
            ref = engine.reflect(prediction=prediction)

            memory_suggestions = []
            if ref.trust_score is not None and ref.trust_score < 0.5:
                memory_suggestions.append("Low trust score - consider manual review")
            if ref.human_review_required:
                memory_suggestions.append("Human review flagged as required")

            elapsed = (time.perf_counter() - start) * 1000

            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result={
                    "trust_score": ref.trust_score,
                    "trust_level": ref.trust_level.value if ref.trust_level else None,
                    "risk_level": ref.risk_level.value if ref.risk_level else None,
                    "human_review_required": ref.human_review_required,
                    "recommendations": [r.value for r in ref.recommendations],
                    "explanations": ref.metadata.get("explainability", {}),
                    "memory_suggestions": memory_suggestions,
                    "question1": question1,
                    "question2": question2,
                    "latency_ms": elapsed,
                },
                confidence=ref.trust_score or 0.0,
                evidence=[
                    {
                        "type": "reflection",
                        "trust_score": ref.trust_score,
                        "trust_level": ref.trust_level.value if ref.trust_level else None,
                        "risk_level": ref.risk_level.value if ref.risk_level else None,
                    }
                ],
                processing_time_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning("ReflectionAgent fell back to basic analysis: %s", e)

            confidence = float(input.get("confidence", 0.0) or prediction.get("confidence", 0.0) or 0.0)
            trust_score = max(0.0, min(1.0, confidence))
            human_review = trust_score < 0.6

            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result={
                    "trust_score": trust_score,
                    "trust_level": "low" if trust_score < 0.5 else "medium" if trust_score < 0.8 else "high",
                    "risk_level": "high" if trust_score < 0.5 else "medium" if trust_score < 0.8 else "low",
                    "human_review_required": human_review,
                    "recommendations": [],
                    "explanations": {},
                    "memory_suggestions": [],
                    "question1": question1,
                    "question2": question2,
                    "latency_ms": elapsed,
                    "fallback": True,
                },
                confidence=trust_score,
                processing_time_ms=elapsed,
            )
