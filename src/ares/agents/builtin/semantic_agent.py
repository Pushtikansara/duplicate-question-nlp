from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput
from ares.semantic_validator import validate_semantic


class SemanticValidatorAgent(Agent):
    metadata = AgentMetadata(
        agent_id="semantic_validator",
        name="Semantic Validator Agent",
        version="1.0",
        description="Validates semantic consistency, detects contradictions, abbreviations, synonyms, and typos",
        capabilities=frozenset(
            {
                AgentCapability.SEMANTIC_UNDERSTANDING,
                AgentCapability.ENTITY_MATCHING,
                AgentCapability.CONFLICT_DETECTION,
            }
        ),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        q1 = input.get("question1", "") or input.get("context", {}).get("question1", "")
        q2 = input.get("question2", "") or input.get("context", {}).get("question2", "")
        prediction_result = input.get("prediction_result") or input.get("context", {}).get("prediction_result")
        if not q1 or not q2:
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error="Both question1 and question2 are required",
                processing_time_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            from ares._result import PredictionResult

            if prediction_result is None:
                prediction_result = PredictionResult(
                    predicted_label=0,
                    prediction="unknown",
                    confidence=0.5,
                    prob_duplicate=0.5,
                    prob_non_duplicate=0.5,
                    model_name="unknown",
                    latency_ms=0,
                )
            result = validate_semantic(q1, q2, prediction_result)
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result=result,
                confidence=result.get("adjusted_confidence", 0.5),
                evidence=[
                    {
                        "type": "semantic_validation",
                        "q1": q1,
                        "q2": q2,
                        "penalty": result.get("semantic_penalty"),
                        "ambiguity": result.get("ambiguity_detected"),
                    }
                ],
                processing_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(status=AgentExecutionStatus.FAILURE, error=str(e), processing_time_ms=elapsed)
