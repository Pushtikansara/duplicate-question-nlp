from __future__ import annotations

from duplicate_question_app._reflection.configuration import ReflectionConfig
from duplicate_question_app._reflection.interfaces import AuditorResult, RiskLevel, TrustLevel


class TrustEngine:
    def __init__(self, config: ReflectionConfig | None = None) -> None:
        self.config = config or ReflectionConfig()

    def compute_trust_score(
        self,
        routing_assessment: AuditorResult | None,
        reasoning_assessment: AuditorResult | None,
        debate_assessment: AuditorResult | None,
        memory_assessment: AuditorResult | None,
        confidence_assessment: AuditorResult | None,
        explainability_score: float,
        evidence_completeness: float,
    ) -> tuple[float, TrustLevel, RiskLevel]:
        weights = self.config.trust_weights
        components: dict[str, float] = {}

        if routing_assessment is not None:
            components["routing_quality"] = routing_assessment.score * weights.get("routing_quality", 0.10)
        if reasoning_assessment is not None:
            components["reasoning_quality"] = reasoning_assessment.score * weights.get("reasoning_quality", 0.20)
        if debate_assessment is not None:
            components["debate_agreement"] = debate_assessment.score * weights.get("debate_agreement", 0.15)
        if confidence_assessment is not None:
            components["confidence_calibration"] = confidence_assessment.score * weights.get(
                "confidence_calibration", 0.15
            )

        mem_weight = weights.get("memory_quality", 0.10)
        if memory_assessment is not None:
            components["memory_quality"] = memory_assessment.score * mem_weight

        exp_weight = weights.get("explainability_completeness", 0.10)
        components["explainability_completeness"] = explainability_score * exp_weight

        ev_weight = weights.get("evidence_completeness", 0.15)
        components["evidence_completeness"] = evidence_completeness * ev_weight

        total_weight = sum(
            weights.get(k, v)
            for k, v in [
                ("routing_quality", 0.10),
                ("reasoning_quality", 0.20),
                ("debate_agreement", 0.15),
                ("confidence_calibration", 0.15),
                ("memory_quality", 0.10),
                ("explainability_completeness", 0.10),
                ("evidence_completeness", 0.15),
                ("benchmark_consistency", 0.05),
            ]
        )

        trust_score = sum(components.values())
        if total_weight > 0:
            trust_score = trust_score / total_weight * 100.0

        trust_level = self._compute_trust_level(trust_score)
        risk_level = self._compute_risk_level(trust_score)
        return trust_score, trust_level, risk_level

    def _compute_trust_level(self, score: float) -> TrustLevel:
        if score >= 80.0:
            return TrustLevel.HIGH
        elif score >= 60.0:
            return TrustLevel.MEDIUM
        elif score >= 40.0:
            return TrustLevel.LOW
        return TrustLevel.CRITICAL

    def _compute_risk_level(self, score: float) -> RiskLevel:
        if score >= 80.0:
            return RiskLevel.LOW
        elif score >= 60.0:
            return RiskLevel.MEDIUM
        elif score >= 40.0:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL
