from __future__ import annotations

from typing import Any


def compute_reasoning_completeness(reasoning_result: Any) -> float:
    if reasoning_result is None:
        return 0.0
    premises = getattr(reasoning_result, "premises", []) or []
    hypotheses = getattr(reasoning_result, "hypotheses", []) or []
    evidence = getattr(reasoning_result, "supporting_evidence", []) or []
    scores = []
    if premises:
        scores.append(min(len(premises) / 5.0, 1.0))
    if hypotheses:
        scores.append(min(len(hypotheses) / 3.0, 1.0))
    if evidence:
        scores.append(min(len(evidence) / 5.0, 1.0))
    return sum(scores) / len(scores) if scores else 0.0


def compute_evidence_completeness(reasoning_result: Any) -> float:
    if reasoning_result is None:
        return 0.0
    supporting = getattr(reasoning_result, "supporting_evidence", []) or []
    contradicting = getattr(reasoning_result, "contradicting_evidence", []) or []
    total = len(supporting) + len(contradicting)
    return min(total / 10.0, 1.0) if total > 0 else 0.0


def compute_debate_completeness(debate_result: Any) -> float:
    if debate_result is None:
        return 0.0
    agents = getattr(debate_result, "agents_used", []) or getattr(debate_result, "agent_results", []) or []
    consensus = getattr(debate_result, "consensus", None)
    votes = getattr(debate_result, "votes", []) or []
    scores = []
    if agents:
        scores.append(min(len(agents) / 8.0, 1.0))
    if consensus is not None:
        scores.append(1.0)
    if votes:
        scores.append(min(len(votes) / 8.0, 1.0))
    return sum(scores) / len(scores) if scores else 0.0


def compute_memory_usage(memory_manager: Any) -> float:
    if memory_manager is None:
        return 0.0
    try:
        stats = memory_manager.get_statistics()
        total = getattr(stats, "total_entries", 0)
        return min(total / 1000.0, 1.0)
    except Exception:
        return 0.0


def compute_explainability_score(
    reasoning_result: Any = None,
    debate_result: Any = None,
    memory_manager: Any = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    if weights is None:
        weights = {"reasoning": 0.3, "evidence": 0.3, "debate": 0.3, "memory": 0.1}
    rc = compute_reasoning_completeness(reasoning_result)
    ec = compute_evidence_completeness(reasoning_result)
    dc = compute_debate_completeness(debate_result)
    mu = compute_memory_usage(memory_manager)
    overall = (
        weights.get("reasoning", 0.3) * rc
        + weights.get("evidence", 0.3) * ec
        + weights.get("debate", 0.3) * dc
        + weights.get("memory", 0.1) * mu
    )
    return {
        "overall": round(overall, 4),
        "reasoning_completeness": round(rc, 4),
        "evidence_completeness": round(ec, 4),
        "debate_completeness": round(dc, 4),
        "memory_usage": round(mu, 4),
        "weights_used": weights,
    }
