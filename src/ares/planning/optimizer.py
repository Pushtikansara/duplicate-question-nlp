from __future__ import annotations

import logging
from typing import Any

from ares.planning.graph import PlanGraph
from ares.planning.types import PlanNode

logger = logging.getLogger(__name__)


class PlanOptimizer:
    def optimize(
        self,
        graph: PlanGraph,
        optimize_latency: bool = True,
        optimize_parallelism: bool = True,
        optimize_cost: bool = False,
        optimize_retries: bool = False,
    ) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "before": self._snapshot(graph),
            "optimizations_applied": [],
        }

        if optimize_parallelism:
            self._optimize_parallelism(graph)
            stats["optimizations_applied"].append("parallelism")

        if optimize_latency:
            self._optimize_latency(graph)
            stats["optimizations_applied"].append("latency")

        if optimize_cost:
            self._optimize_cost(graph)
            stats["optimizations_applied"].append("cost")

        if optimize_retries:
            self._optimize_retries(graph)
            stats["optimizations_applied"].append("retries")

        stats["after"] = self._snapshot(graph)
        stats["improvements"] = self._compute_improvements(stats["before"], stats["after"])
        graph.plan.optimization_stats = stats

        logger.info(
            "Optimization applied: %s | Latency improvement: %.1f%%",
            ", ".join(stats["optimizations_applied"]),
            stats["improvements"].get("latency_pct", 0),
        )

        return stats

    def _optimize_parallelism(self, graph: PlanGraph) -> None:
        levels = graph.get_execution_order()
        for level in levels:
            level_nodes = [graph.plan.nodes[nid] for nid in level if nid in graph.plan.nodes]
            independent_groups = self._find_independent_groups(level_nodes, graph)
            for group in independent_groups:
                if len(group) > 1:
                    for node in group:
                        node.metadata["parallel"] = True
                        node.metadata["parallel_group"] = id(group)

    def _find_independent_groups(self, nodes: list[PlanNode], graph: PlanGraph) -> list[list[PlanNode]]:
        groups: list[list[PlanNode]] = []
        for node in nodes:
            added = False
            for group in groups:
                if all(
                    not graph._would_create_cycle(n.node_id, node.node_id)
                    and not graph._would_create_cycle(node.node_id, n.node_id)
                    for n in group
                ):
                    group.append(node)
                    added = True
                    break
            if not added:
                groups.append([node])
        return groups

    def _optimize_latency(self, graph: PlanGraph) -> None:
        levels = graph.get_execution_order()
        for level in levels:
            level_nodes = [graph.plan.nodes[nid] for nid in level if nid in graph.plan.nodes]
            slow_nodes = sorted(level_nodes, key=lambda n: n.latency_estimate_ms, reverse=True)
            if len(slow_nodes) >= 2:
                for node in slow_nodes[: len(slow_nodes) // 2]:
                    node.metadata["priority"] = "high"

    def _optimize_cost(self, graph: PlanGraph) -> None:
        for node in graph.plan.nodes.values():
            if node.cost_estimate > 0:
                node.metadata["cost_optimized"] = True
                if node.cost_estimate > 10.0 and node.max_retries > 1:
                    node.max_retries = max(1, node.max_retries - 1)
                    node.metadata["retries_reduced"] = True

    def _optimize_retries(self, graph: PlanGraph) -> None:
        for node in graph.plan.nodes.values():
            estimated_duration = node.latency_estimate_ms / 1000.0
            if estimated_duration < 5.0:
                node.max_retries = min(3, node.max_retries + 1)
                node.metadata["retry_optimized"] = True

    def _snapshot(self, graph: PlanGraph) -> dict[str, Any]:
        return {
            "node_count": len(graph.plan.nodes),
            "edge_count": len(graph.plan.edges),
            "total_latency_estimate_ms": sum(n.latency_estimate_ms for n in graph.plan.nodes.values()),
            "total_cost_estimate": sum(n.cost_estimate for n in graph.plan.nodes.values()),
            "max_depth": len(graph.get_execution_order()),
            "parallel_nodes": sum(1 for n in graph.plan.nodes.values() if n.metadata.get("parallel")),
        }

    def _compute_improvements(self, before: dict, after: dict) -> dict[str, float]:
        improvements: dict[str, float] = {}
        for key in ("total_latency_estimate_ms", "total_cost_estimate", "max_depth"):
            b = before.get(key, 0) or 0.001
            a = after.get(key, 0)
            improvements[f"{key}_pct"] = ((b - a) / b) * 100
        before_parallel = before.get("parallel_nodes", 0)
        after_parallel = after.get("parallel_nodes", 0)
        if before_parallel > 0:
            improvements["parallelism_pct"] = (after_parallel - before_parallel) / before_parallel * 100
        else:
            improvements["parallelism_pct"] = 0.0
        return improvements
