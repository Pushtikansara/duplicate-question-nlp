from __future__ import annotations

from typing import Any


def compute_debate_metrics(debate_results: list[Any]) -> dict[str, Any]:
    if not debate_results:
        return {
            "avg_agent_agreement": 0.0,
            "avg_consensus_confidence": 0.0,
            "conflict_frequency": 0.0,
            "avg_debate_duration_ms": 0.0,
            "total_debates": 0,
        }
    agreements = []
    confidences = []
    conflicts = 0
    durations = []
    for r in debate_results:
        am = getattr(r, "agreement_matrix", None)
        if am is not None:
            agreements.append(
                float(
                    getattr(am, "mean_agreement", lambda: 0.0)()
                    if callable(getattr(am, "mean_agreement", None))
                    else 0.0
                )
            )
        consensus = getattr(r, "consensus", None)
        if consensus is not None:
            confidences.append(float(getattr(consensus, "confidence", 0.0)))
        conflicts += len(getattr(r, "conflict_reports", []) or [])
        durations.append(float(getattr(r, "processing_time_ms", 0.0)))
    return {
        "avg_agent_agreement": sum(agreements) / len(agreements) if agreements else 0.0,
        "avg_consensus_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "conflict_frequency": conflicts / len(debate_results) if debate_results else 0.0,
        "avg_debate_duration_ms": sum(durations) / len(durations) if durations else 0.0,
        "total_debates": len(debate_results),
    }
