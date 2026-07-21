from __future__ import annotations

from typing import Any


class ExplainabilityEngine:
    def generate(self, context: Any, trust_score: float, assessments: dict[str, Any]) -> dict[str, Any]:
        human_readable = self._generate_human_readable(context, trust_score, assessments)
        technical = self._generate_technical(context, trust_score, assessments)
        module_contributions = self._compute_module_contributions(assessments)
        return {
            "human_readable": human_readable,
            "technical": technical,
            "module_contributions": module_contributions,
        }

    def _generate_human_readable(self, context: Any, trust_score: float, assessments: dict) -> str:
        lines: list[str] = []
        if trust_score >= 80:
            lines.append("Prediction can be trusted with high confidence.")
        elif trust_score >= 60:
            lines.append("Prediction is moderately trustworthy.")
        elif trust_score >= 40:
            lines.append("Prediction should be treated with caution.")
        else:
            lines.append("Prediction cannot be trusted without human review.")

        routing = assessments.get("routing")
        if routing is not None:
            score = getattr(routing, "score", 0.0)
            if score >= 0.8:
                lines.append("The routing pipeline selection was appropriate.")
            elif score < 0.5:
                lines.append("The routing pipeline may not have been optimal.")

        reasoning = assessments.get("reasoning")
        if reasoning is not None:
            score = getattr(reasoning, "score", 0.0)
            details = getattr(reasoning, "details", {})
            ev_count = details.get("supporting_evidence_count", 0)
            if ev_count > 0:
                lines.append(f"The reasoning process found {ev_count} pieces of supporting evidence.")

        debate = assessments.get("debate")
        if debate is not None:
            score = getattr(debate, "score", 0.0)
            details = getattr(debate, "details", {})
            agent_count = details.get("agent_count", 0)
            conflict_count = details.get("conflict_count", 0)
            lines.append(f"The debate involved {agent_count} agents with {conflict_count} conflicts identified.")

        return " ".join(lines)

    def _generate_technical(self, context: Any, trust_score: float, assessments: dict) -> str:
        parts: list[str] = [f"TrustScore={trust_score:.1f}"]
        for name, assessment in assessments.items():
            if assessment is not None:
                score = getattr(assessment, "score", 0.0)
                parts.append(f"{name.capitalize()}={score:.2f}")
        return " | ".join(parts)

    def _compute_module_contributions(self, assessments: dict) -> dict[str, float]:
        contributions: dict[str, float] = {}
        for name, assessment in assessments.items():
            if assessment is not None:
                contributions[name] = getattr(assessment, "score", 0.0)
        return contributions
