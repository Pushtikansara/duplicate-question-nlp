from __future__ import annotations

import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import AgentCapability, AgentExecutionStatus, AgentMetadata, AgentOutput


class ExplainabilityAgent(Agent):
    metadata = AgentMetadata(
        agent_id="explainability",
        name="Explainability Agent",
        version="1.0",
        description="Generates human-readable explanations for predictions, confidence, and trust",
        capabilities=frozenset({AgentCapability.REASONING, AgentCapability.CONFIDENCE_ASSESSMENT}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        prediction = input.get("prediction", {})
        semantic = input.get("semantic_validation", {})
        reflection = input.get("reflection", {})
        confidence_detail = input.get("confidence_calculation", {})

        explanations = {
            "prediction_summary": f"Model predicted '{prediction.get('prediction')}' with {prediction.get('confidence', 0):.1%} raw confidence",
            "confidence_explanation": self._explain_confidence(confidence_detail),
            "semantic_explanation": self._explain_semantic(semantic),
            "trust_explanation": self._explain_trust(reflection),
            "model_used": prediction.get("model_name", "unknown"),
        }

        elapsed = (time.perf_counter() - start) * 1000
        return self.create_output(
            status=AgentExecutionStatus.SUCCESS,
            result=explanations,
            confidence=prediction.get("confidence", 0.5),
            evidence=[{"type": "explainability", "explanations": explanations}],
            processing_time_ms=elapsed,
        )

    def _explain_confidence(self, cd: dict[str, Any]) -> str:
        if not cd:
            return "Confidence calculation not available"
        parts = []
        if "raw_confidence" in cd:
            parts.append(f"raw confidence: {cd['raw_confidence']:.1%}")
        if "adjusted_confidence" in cd:
            parts.append(f"semantically adjusted: {cd['adjusted_confidence']:.1%}")
        if "agreement_score" in cd:
            parts.append(f"model agreement: {cd['agreement_score']:.1%}")
        if "final_confidence" in cd:
            parts.append(f"final: {cd['final_confidence']:.1%}")
        return " → ".join(parts)

    def _explain_semantic(self, s: dict[str, Any]) -> str:
        if not s:
            return "No semantic validation performed"
        if s.get("ambiguity_detected"):
            return f"Semantic ambiguity detected: {s.get('reasoning', 'unknown')}"
        return "No semantic issues detected"

    def _explain_trust(self, r: dict[str, Any]) -> str:
        if not r:
            return "Trust assessment not available"
        return f"Trust score: {r.get('trust_score', 0):.1%} ({r.get('trust_level', 'unknown')})"
