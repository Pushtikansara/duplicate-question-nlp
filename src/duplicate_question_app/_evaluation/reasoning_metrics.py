from __future__ import annotations

from typing import Any


def compute_reasoning_metrics(reasoning_results: list[Any]) -> dict[str, Any]:
    if not reasoning_results:
        return {
            "avg_premise_count": 0.0,
            "avg_hypothesis_count": 0.0,
            "avg_evidence_chain_length": 0.0,
            "avg_confidence": 0.0,
            "avg_uncertainty": 0.0,
            "total_reasoned": 0,
        }
    premises = []
    hypotheses = []
    evidence_lengths = []
    confidences = []
    uncertainties = []
    for r in reasoning_results:
        premises.append(len(getattr(r, "premises", []) or []))
        hypotheses.append(len(getattr(r, "hypotheses", []) or []))
        supporting = getattr(r, "supporting_evidence", []) or []
        contradicting = getattr(r, "contradicting_evidence", []) or []
        evidence_lengths.append(len(supporting) + len(contradicting))
        confidences.append(float(getattr(r, "confidence", 0.0)))
        uncertainties.append(float(getattr(r, "uncertainty", 1.0)))
    return {
        "avg_premise_count": sum(premises) / len(premises),
        "avg_hypothesis_count": sum(hypotheses) / len(hypotheses),
        "avg_evidence_chain_length": sum(evidence_lengths) / len(evidence_lengths),
        "avg_confidence": sum(confidences) / len(confidences),
        "avg_uncertainty": sum(uncertainties) / len(uncertainties),
        "total_reasoned": len(reasoning_results),
    }
