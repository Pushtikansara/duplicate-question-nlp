from __future__ import annotations


class TestPlanOptimizer:
    def test_optimize_parallelism(self, optimizer, sample_graph) -> None:
        stats = optimizer.optimize(sample_graph, optimize_latency=False, optimize_parallelism=True)
        assert "parallelism" in stats["optimizations_applied"]
        assert "before" in stats
        assert "after" in stats

    def test_optimize_latency(self, optimizer, sample_graph) -> None:
        stats = optimizer.optimize(sample_graph, optimize_latency=True, optimize_parallelism=False)
        assert "latency" in stats["optimizations_applied"]

    def test_optimize_cost(self, optimizer, sample_graph) -> None:
        for n in sample_graph.plan.nodes.values():
            n.cost_estimate = 15.0
            n.latency_estimate_ms = 100.0
        stats = optimizer.optimize(sample_graph, optimize_cost=True, optimize_latency=False, optimize_parallelism=False)
        assert "cost" in stats["optimizations_applied"]

    def test_optimize_retries(self, optimizer, sample_graph) -> None:
        for n in sample_graph.plan.nodes.values():
            n.latency_estimate_ms = 1000.0
        stats = optimizer.optimize(
            sample_graph, optimize_retries=True, optimize_latency=False, optimize_parallelism=False
        )
        assert "retries" in stats["optimizations_applied"]

    def test_optimize_all(self, optimizer, sample_graph) -> None:
        stats = optimizer.optimize(sample_graph)
        assert len(stats["optimizations_applied"]) >= 2

    def test_snapshot(self, optimizer, sample_graph) -> None:
        snap = optimizer._snapshot(sample_graph)
        assert snap["node_count"] == 3
        assert snap["edge_count"] == 2
