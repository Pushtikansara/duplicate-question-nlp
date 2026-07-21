from __future__ import annotations

from typing import Any


class EvidenceAnalyzer:
    def analyze(self, reasoning_result: Any, debate_result: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            "total_evidence": 0,
            "supporting_count": 0,
            "contradicting_count": 0,
            "evidence_types": {},
            "completeness": 0.0,
        }

        if reasoning_result is not None:
            supporting = getattr(reasoning_result, "supporting_evidence", []) or []
            contradicting = getattr(reasoning_result, "contradicting_evidence", []) or []
            result["supporting_count"] = len(supporting)
            result["contradicting_count"] = len(contradicting)
            result["total_evidence"] = len(supporting) + len(contradicting)

            for ev in supporting + contradicting:
                ev_type = getattr(ev, "type", "unknown") if not isinstance(ev, dict) else ev.get("type", "unknown")
                result["evidence_types"][ev_type] = result["evidence_types"].get(ev_type, 0) + 1

        if debate_result is not None:
            agent_results = getattr(debate_result, "agent_results", []) or []
            for agent in agent_results:
                agent_supporting = getattr(agent, "supporting_evidence", []) or []
                agent_contra = getattr(agent, "contradicting_evidence", []) or []
                result["total_evidence"] += len(agent_supporting) + len(agent_contra)
                result["supporting_count"] += len(agent_supporting)
                result["contradicting_count"] += len(agent_contra)

        total = result["total_evidence"]
        result["completeness"] = min(total / 20.0, 1.0)
        return result
