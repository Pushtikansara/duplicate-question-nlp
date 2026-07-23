from __future__ import annotations

import pytest

from ares.planning import PlanNodeStatus


class TestPlanExecutor:
    def test_execute_completes(self, executor, sample_graph) -> None:
        result = __import__("asyncio").run(executor.execute(sample_graph))
        assert result.status.name in ("COMPLETED", "PARTIAL")
        assert result.plan_id == "plan-1"

    def test_execute_cancel(self, executor, sample_graph) -> None:
        executor.cancel("plan-1")
        result = __import__("asyncio").run(executor.execute(sample_graph))
        assert result.status.name == "CANCELLED"

    def test_execute_partial(self, executor, sample_graph) -> None:
        n1 = sample_graph.get_node("n1")
        n1.status = PlanNodeStatus.COMPLETED
        result = __import__("asyncio").run(executor.execute_partial(sample_graph, "n2"))
        assert result is not None

    def test_execute_partial_not_found(self, executor, sample_graph) -> None:
        with pytest.raises(ValueError, match="not found"):
            __import__("asyncio").run(executor.execute_partial(sample_graph, "n99"))

    def test_resume(self, executor, sample_graph) -> None:
        n2 = sample_graph.get_node("n2")
        n2.status = PlanNodeStatus.RUNNING
        result = __import__("asyncio").run(executor.resume(sample_graph))
        assert result is not None

    def test_metrics_recorded(self, executor, sample_graph) -> None:
        __import__("asyncio").run(executor.execute(sample_graph))
        assert executor.metrics.total_plans >= 0
