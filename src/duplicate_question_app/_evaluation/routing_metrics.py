from __future__ import annotations

from typing import Any


def compute_routing_metrics(routing_results: list[Any]) -> dict[str, Any]:
    if not routing_results:
        return {
            "pipeline_selections": {},
            "complexity_distribution": {},
            "uncertainty_escalations": 0,
            "avg_latency_ms": 0.0,
            "total_routes": 0,
        }
    pipeline_counts: dict[str, int] = {}
    complexity_counts: dict[str, int] = {}
    uncertain_count = 0
    latencies: list[float] = []
    for r in routing_results:
        pipeline = getattr(r, "selected_pipeline", "unknown")
        pipeline_counts[pipeline] = pipeline_counts.get(pipeline, 0) + 1
        complexity = getattr(r, "complexity", "unknown")
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        if getattr(r, "uncertainty_result", None) is not None:
            uncertain_count += 1
        meta = getattr(r, "metadata", {}) or {}
        latencies.append(float(meta.get("routing_latency_ms", 0.0)))
    return {
        "pipeline_selections": pipeline_counts,
        "complexity_distribution": complexity_counts,
        "uncertainty_escalations": uncertain_count,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "total_routes": len(routing_results),
    }
