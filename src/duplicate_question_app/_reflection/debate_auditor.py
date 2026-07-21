from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import AuditorResult, DebateAuditorABC


class DebateAuditor(DebateAuditorABC):
    def audit(self, debate_result: Any) -> AuditorResult:
        if debate_result is None:
            return AuditorResult(
                module="debate",
                score=0.5,
                details={"available": False},
                warnings=["No debate result available"],
                passed=False,
            )
        details: dict[str, Any] = {}
        warnings: list[str] = []
        score = 1.0

        agent_results = getattr(debate_result, "agent_results", []) or []
        votes = getattr(debate_result, "votes", []) or []
        conflicts = getattr(debate_result, "conflict_reports", []) or []
        consensus = getattr(debate_result, "consensus", None)

        details["agent_count"] = len(agent_results)
        details["vote_count"] = len(votes)
        details["conflict_count"] = len(conflicts)
        details["consensus_available"] = consensus is not None

        if len(agent_results) < 4:
            score -= 0.15
            warnings.append(f"Low agent participation: {len(agent_results)}/8")
        if len(conflicts) > 3:
            score -= 0.15 * min(len(conflicts) / 5.0, 1.0)
            warnings.append(f"High conflict count: {len(conflicts)}")

        if consensus is not None:
            cons_conf = float(getattr(consensus, "confidence", 0.0))
            details["consensus_confidence"] = cons_conf
            if cons_conf < 0.5:
                score -= 0.2
                warnings.append(f"Low consensus confidence: {cons_conf:.2f}")
        else:
            score -= 0.3
            warnings.append("No consensus reached")

        agreement_matrix = getattr(debate_result, "agreement_matrix", None)
        if agreement_matrix is not None:
            mean_agreement = getattr(agreement_matrix, "mean_agreement", None)
            if callable(mean_agreement):
                details["mean_agreement"] = mean_agreement()
            elif mean_agreement is not None:
                details["mean_agreement"] = mean_agreement
            if details.get("mean_agreement", 1.0) < 0.5:
                score -= 0.2
                warnings.append("Low mean agent agreement")

        score = max(0.0, min(1.0, score))
        return AuditorResult(
            module="debate",
            score=score,
            details=details,
            warnings=warnings,
            passed=score >= 0.5,
        )
