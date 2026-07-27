from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput
from ares.confidence import compute_calibration_score, compute_final_confidence
from ares.semantic_validator import validate_semantic


class CalibrationAgent(Agent):
    metadata = AgentMetadata(
        agent_id="calibration",
        name="Calibration Agent",
        version="1.0",
        description="Calibrates prediction confidence using semantic validation and model agreement",
        capabilities=frozenset({AgentCapability.CONFIDENCE_ASSESSMENT}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        q1 = input.get("question1", "")
        q2 = input.get("question2", "")
        prediction = input.get("prediction", {})
        mode = input.get("mode", "selected")

        if not prediction:
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error="No prediction data provided",
                processing_time_ms=(time.perf_counter() - start) * 1000,
            )

        try:
            raw_conf = prediction.get("confidence", 0.5)
            semantic_result = validate_semantic(q1, q2, type("PR", (), {"confidence": raw_conf})())
            adjusted_conf = semantic_result["adjusted_confidence"]
            agreement = prediction.get("agreement_score")
            trust_score = prediction.get("trust_score")
            uncertainty = prediction.get("uncertainty")

            confidence_result = compute_final_confidence(
                raw_confidence=raw_conf,
                adjusted_confidence=adjusted_conf,
                agreement_score=agreement,
                trust_score=trust_score,
                uncertainty=uncertainty,
                mode=mode,
            )

            calibration_score = compute_calibration_score(confidence_result["final_confidence"])

            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(
                status=AgentExecutionStatus.SUCCESS,
                result={
                    **confidence_result,
                    "calibration_score": calibration_score,
                    "semantic_validation": semantic_result,
                },
                confidence=confidence_result["final_confidence"],
                processing_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return self.create_output(status=AgentExecutionStatus.FAILURE, error=str(e), processing_time_ms=elapsed)
