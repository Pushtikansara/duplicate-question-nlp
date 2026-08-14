from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ares.adaptive.config_loader import AdaptiveRoutingConfig
from ares.adaptive.models import DifficultyAssessment, ModelEvidence, ModelProfile
from ares.adaptive.profiles import ModelProfileRegistry


@dataclass
class TrustAssessment:
    """A first-class, traceable assessment of whether a model's answer can be
    trusted, and whether a stronger model must verify it.

    Replaces the previous inline ``_trust_risk`` helper in the executor so the
    logic is unit-testable in isolation and surfaced through the trace. Produced
    deterministically from configuration, difficulty signals and model
    reliability — no randomness, no external LLM.
    """

    trust_score: float = 1.0
    trust_level: str = "high"  # low / medium / high
    escalation_required: bool = False
    escalation_reasons: list[str] = field(default_factory=list)
    risk_reasons: list[str] = field(default_factory=list)
    reliability: float = 1.0
    evidence: ModelEvidence | None = None
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_score": round(self.trust_score, 4),
            "trust_level": self.trust_level,
            "escalation_required": self.escalation_required,
            "escalation_reasons": list(self.escalation_reasons),
            "risk_reasons": list(self.risk_reasons),
            "reliability": round(self.reliability, 4),
            "evidence_model": self.evidence.model_name if self.evidence else None,
            "explanation": self.explanation,
        }


#: Structural reasons that a cheap lexical model cannot judge and which, on
#: their own, mandate re-verification with a stronger model.  Tunable through
#: config (``trust.escalation_reasons``) if a deployment wants more or fewer.
DEFAULT_ESCALATION_REASONS = frozenset({"abbreviation_relation", "content_mismatch_duplicate"})


class TrustAnalyzer:
    """Computes trust for one initial model prediction.

    Trust starts at 1.0 and is reduced by:

    * structural difficulty signals the cheap model cannot judge (acronym
      relation, content mismatch, contradiction, negation, numeric conflict);
    * the reliability of the model that produced the prediction (from the
      model profile, an estimated figure marked as provisional in config);
    * low prediction confidence.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        profile_registry: ModelProfileRegistry | None = None,
    ) -> None:
        self._config = AdaptiveRoutingConfig(config)
        self._profiles = profile_registry or ModelProfileRegistry(config)
        cfg_escalation = getattr(self._config, "trust_escalation_reasons", None)
        self._escalation_reasons = frozenset(cfg_escalation) if cfg_escalation else DEFAULT_ESCALATION_REASONS

    def assess(
        self,
        assessment: DifficultyAssessment,
        evidence: ModelEvidence | None = None,
    ) -> TrustAssessment:
        signals = assessment.signals or {}
        reasons: list[str] = []
        risk_reasons: list[str] = []
        deduction = 0.0

        ab_rel = float(signals.get("abbreviation_relation", 0.0) or 0.0)
        if ab_rel >= self._config.trust_abbreviation_relation_min:
            risk_reasons.append("abbreviation_relation")
            reasons.append("abbreviation_relation")
            deduction += 0.35

        content_overlap = signals.get("content_overlap")
        content_overlap = None if content_overlap is None else float(content_overlap)
        if (
            evidence is not None
            and evidence.predicted_label == 1
            and content_overlap is not None
            and content_overlap <= self._config.trust_content_mismatch_max
        ):
            risk_reasons.append("content_mismatch_duplicate")
            reasons.append("content_mismatch_duplicate")
            deduction += 0.45

        if float(signals.get("contradiction", 0.0) or 0.0) >= 0.5:
            risk_reasons.append("contradiction")
            deduction += 0.20
        if float(signals.get("negation", 0.0) or 0.0) >= 0.5:
            risk_reasons.append("negation")
            deduction += 0.15
        if float(signals.get("numeric_conflict", 0.0) or 0.0) >= 0.9:
            risk_reasons.append("numeric_conflict")
            deduction += 0.15

        reliability = 1.0
        model_name = evidence.model_name if evidence is not None else None
        profile = self._profile(model_name)
        if profile is not None:
            reliability = float(profile.reliability)
            deduction += max(0.0, (1.0 - reliability) * 1.0)
            if reliability < self._config.trust_reliability_min:
                risk_reasons.append("low_model_reliability")

        if (
            evidence is not None
            and evidence.confidence is not None
            and evidence.confidence < self._config.confidence_min_evident
        ):
            risk_reasons.append("low_confidence")
            deduction += 0.10

        trust_score = max(0.0, min(1.0, 1.0 - deduction))
        trust_level = self._level(trust_score)
        escalation_required = bool(self._escalation_reasons.intersection(risk_reasons))

        if evidence is None:
            explanation = "no model evidence yet; trust is provisional"
        else:
            explanation = (
                f"trust={trust_score:.2f} ({trust_level}); "
                f"model={evidence.model_name} reliability={reliability:.2f}; "
                + (f"risks={', '.join(risk_reasons)}" if risk_reasons else "no risk signals")
            )

        return TrustAssessment(
            trust_score=round(trust_score, 4),
            trust_level=trust_level,
            escalation_required=escalation_required,
            escalation_reasons=[r for r in risk_reasons if r in self._escalation_reasons],
            risk_reasons=risk_reasons,
            reliability=round(reliability, 4),
            evidence=evidence,
            explanation=explanation,
        )

    def _level(self, trust_score: float) -> str:
        if trust_score >= self._config.trust_high_threshold:
            return "high"
        if trust_score >= self._config.trust_low_threshold:
            return "medium"
        return "low"

    def _profile(self, model_name: str | None) -> ModelProfile | None:
        if not model_name:
            return None
        return self._profiles.get(model_name)
