from __future__ import annotations

from typing import Any


class PlanningMetrics:
    def __init__(self) -> None:
        self._planning_latencies: list[float] = []
        self._execution_latencies: list[float] = []
        self._optimization_gains: list[dict[str, float]] = []
        self._failures: int = 0
        self._retries: int = 0
        self._plans_created: int = 0
        self._plans_completed: int = 0
        self._plans_failed: int = 0
        self._node_counts: list[int] = []
        self._edge_counts: list[int] = []

    def record_planning_latency(self, latency_ms: float) -> None:
        self._planning_latencies.append(latency_ms)

    def record_execution_latency(self, latency_ms: float) -> None:
        self._execution_latencies.append(latency_ms)

    def record_optimization_gain(self, before: float, after: float, metric: str = "latency") -> None:
        gain = ((before - after) / before * 100) if before > 0 else 0.0
        self._optimization_gains.append({"metric": metric, "before": before, "after": after, "gain_pct": gain})

    def record_failure(self) -> None:
        self._failures += 1
        self._plans_failed += 1

    def record_retry(self) -> None:
        self._retries += 1

    def record_plan_created(self, node_count: int, edge_count: int) -> None:
        self._plans_created += 1
        self._node_counts.append(node_count)
        self._edge_counts.append(edge_count)

    def record_plan_completed(self) -> None:
        self._plans_completed += 1

    @property
    def avg_planning_latency_ms(self) -> float:
        if not self._planning_latencies:
            return 0.0
        return sum(self._planning_latencies) / len(self._planning_latencies)

    @property
    def avg_execution_latency_ms(self) -> float:
        if not self._execution_latencies:
            return 0.0
        return sum(self._execution_latencies) / len(self._execution_latencies)

    @property
    def failure_rate(self) -> float:
        total = self._plans_created
        if total == 0:
            return 0.0
        return self._plans_failed / total

    @property
    def avg_optimization_gain_pct(self) -> float:
        if not self._optimization_gains:
            return 0.0
        return sum(g["gain_pct"] for g in self._optimization_gains) / len(self._optimization_gains)

    @property
    def avg_node_count(self) -> float:
        if not self._node_counts:
            return 0.0
        return sum(self._node_counts) / len(self._node_counts)

    @property
    def total_plans(self) -> int:
        return self._plans_created

    @property
    def total_retries(self) -> int:
        return self._retries

    def summary(self) -> dict[str, Any]:
        return {
            "plans_created": self._plans_created,
            "plans_completed": self._plans_completed,
            "plans_failed": self._plans_failed,
            "failure_rate": self.failure_rate,
            "avg_planning_latency_ms": self.avg_planning_latency_ms,
            "avg_execution_latency_ms": self.avg_execution_latency_ms,
            "avg_node_count": self.avg_node_count,
            "total_retries": self._retries,
            "avg_optimization_gain_pct": self.avg_optimization_gain_pct,
        }

    def reset(self) -> None:
        self.__init__()
