from __future__ import annotations

from ares.agents.types import AgentExecutionStatus, AgentOutput
from ares.orchestration.aggregator import ResultAggregator
from ares.orchestration.types import (
    OrchestrationStatus,
    SharedAgentContext,
    TaskNode,
    TaskStatus,
)


class TestResultAggregator:
    def test_collect_all_completed(self):
        agg = ResultAggregator()
        nodes = {
            "a": TaskNode(
                id="a",
                agent_id="a",
                status=TaskStatus.COMPLETED,
                output=AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"key": "val"}),
                processing_time_ms=10.0,
            ),
            "b": TaskNode(
                id="b",
                agent_id="b",
                status=TaskStatus.COMPLETED,
                output=AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"key2": "val2"}),
                processing_time_ms=20.0,
            ),
        }
        ctx = SharedAgentContext()
        result = agg.collect_results(nodes, ctx, workflow_id="wf_1")
        assert result.status == OrchestrationStatus.COMPLETED
        assert result.workflow_id == "wf_1"
        assert len(result.agent_results) == 2

    def test_collect_partial_failure(self):
        agg = ResultAggregator()
        nodes = {
            "a": TaskNode(
                id="a",
                agent_id="a",
                status=TaskStatus.COMPLETED,
                output=AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"ok": True}),
            ),
            "b": TaskNode(
                id="b",
                agent_id="b",
                status=TaskStatus.FAILED,
                output=AgentOutput(agent_id="b", status=AgentExecutionStatus.FAILURE, error="boom"),
                error="boom",
            ),
        }
        ctx = SharedAgentContext()
        result = agg.collect_results(nodes, ctx)
        assert result.status == OrchestrationStatus.PARTIAL
        assert "boom" in (result.error or "")

    def test_collect_all_failed(self):
        agg = ResultAggregator()
        nodes = {
            "a": TaskNode(
                id="a",
                agent_id="a",
                status=TaskStatus.FAILED,
                error="fail_a",
            ),
            "b": TaskNode(
                id="b",
                agent_id="b",
                status=TaskStatus.FAILED,
                error="fail_b",
            ),
        }
        ctx = SharedAgentContext()
        result = agg.collect_results(nodes, ctx)
        assert result.status == OrchestrationStatus.FAILED

    def test_collect_cancelled(self):
        agg = ResultAggregator()
        nodes = {
            "a": TaskNode(id="a", agent_id="a", status=TaskStatus.CANCELLED),
        }
        ctx = SharedAgentContext()
        result = agg.collect_results(nodes, ctx)
        assert result.status == OrchestrationStatus.CANCELLED

    def test_collect_timeout(self):
        agg = ResultAggregator()
        nodes = {
            "a": TaskNode(id="a", agent_id="a", status=TaskStatus.TIMEOUT),
        }
        ctx = SharedAgentContext()
        result = agg.collect_results(nodes, ctx)
        assert result.status == OrchestrationStatus.PARTIAL

    def test_merge_concat(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"items": [1, 2], "name": "a"}),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"items": [3], "name": "b"}),
        ]
        merged = agg.merge_outputs(outputs, "concat")
        assert merged["items"] == [1, 2, 3]
        assert merged["name"] == "b"

    def test_merge_first(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"x": 1}),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"x": 2}),
        ]
        merged = agg.merge_outputs(outputs, "first")
        assert merged == {"x": 1}

    def test_merge_last(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"x": 1}),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"x": 2}),
        ]
        merged = agg.merge_outputs(outputs, "last")
        assert merged == {"x": 2}

    def test_merge_empty(self):
        agg = ResultAggregator()
        assert agg.merge_outputs([], "concat") == {}

    def test_merge_weighted(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"score": 10}, confidence=0.8),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"score": 20}, confidence=0.2),
        ]
        merged = agg.merge_outputs(outputs, "weighted")
        assert merged["score"] == 12.0

    def test_select_best_by_confidence(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"v": 1}, confidence=0.5),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"v": 2}, confidence=0.9),
        ]
        best = agg.select_best_output(outputs, by="confidence")
        assert best is not None
        assert best.agent_id == "b"
        assert best.result == {"v": 2}

    def test_select_best_first(self):
        agg = ResultAggregator()
        outputs = [
            AgentOutput(agent_id="a", status=AgentExecutionStatus.SUCCESS, result={"v": 1}),
            AgentOutput(agent_id="b", status=AgentExecutionStatus.SUCCESS, result={"v": 2}),
        ]
        best = agg.select_best_output(outputs, by="first")
        assert best is not None
        assert best.agent_id == "a"

    def test_select_best_empty(self):
        agg = ResultAggregator()
        assert agg.select_best_output([], by="confidence") is None
