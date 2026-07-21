from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import ConsistencyWarning


class ConsistencyChecker:
    def check(
        self,
        reasoning_result: Any,
        debate_result: Any,
        prediction: dict[str, Any],
    ) -> list[ConsistencyWarning]:
        warnings: list[ConsistencyWarning] = []
        if reasoning_result is not None:
            warnings.extend(self._check_reasoning_consistency(reasoning_result))
        if debate_result is not None:
            warnings.extend(self._check_debate_consistency(debate_result))
        if reasoning_result is not None and debate_result is not None:
            warnings.extend(self._check_cross_module_consistency(reasoning_result, debate_result, prediction))
        return warnings

    def _check_reasoning_consistency(self, reasoning_result: Any) -> list[ConsistencyWarning]:
        warnings: list[ConsistencyWarning] = []
        supporting = getattr(reasoning_result, "supporting_evidence", []) or []
        contradicting = getattr(reasoning_result, "contradicting_evidence", []) or []
        if len(supporting) > 0 and len(contradicting) > 0:
            ratio = len(contradicting) / max(len(supporting), 1)
            if ratio > 0.5:
                warnings.append(
                    ConsistencyWarning(
                        warning_type="conflicting_evidence",
                        description=f"Contradicting evidence ({len(contradicting)}) is significant vs supporting ({len(supporting)})",
                        severity=min(ratio, 1.0),
                        details={"supporting": len(supporting), "contradicting": len(contradicting)},
                    )
                )
        return warnings

    def _check_debate_consistency(self, debate_result: Any) -> list[ConsistencyWarning]:
        warnings: list[ConsistencyWarning] = []
        conflicts = getattr(debate_result, "conflict_reports", []) or []
        if len(conflicts) > 3:
            warnings.append(
                ConsistencyWarning(
                    warning_type="high_debate_conflict",
                    description=f"Debate produced {len(conflicts)} conflicts",
                    severity=min(len(conflicts) / 10.0, 1.0),
                    details={"conflict_count": len(conflicts)},
                )
            )

        votes_list = getattr(debate_result, "votes", []) or []
        recommendations = [getattr(v, "recommendation", None) for v in votes_list]
        unique_recs = {r for r in recommendations if r is not None}
        if len(unique_recs) > 1:
            warnings.append(
                ConsistencyWarning(
                    warning_type="vote_disagreement",
                    description=f"Agents disagree on recommendation: {unique_recs}",
                    severity=0.6,
                    details={"recommendations": list(unique_recs)},
                )
            )
        return warnings

    def _check_cross_module_consistency(
        self,
        reasoning_result: Any,
        debate_result: Any,
        prediction: dict[str, Any],
    ) -> list[ConsistencyWarning]:
        warnings: list[ConsistencyWarning] = []
        reasoning_decision = getattr(reasoning_result, "decision", "uncertain")
        consensus = getattr(debate_result, "consensus", None)
        debate_decision = getattr(consensus, "decision", "uncertain") if consensus else "uncertain"
        pred_label = prediction.get("predicted_label", -1)
        pred_str = "duplicate" if pred_label == 1 else "not_duplicate" if pred_label == 0 else "unknown"

        decisions = [reasoning_decision.lower(), debate_decision.lower(), pred_str]
        if len(set(decisions)) > 1:
            warnings.append(
                ConsistencyWarning(
                    warning_type="cross_module_inconsistency",
                    description=f"Modules disagree: Reasoning={reasoning_decision}, Debate={debate_decision}, Final={pred_str}",
                    severity=0.7,
                    details={"reasoning": reasoning_decision, "debate": debate_decision, "final": pred_str},
                )
            )
        return warnings
