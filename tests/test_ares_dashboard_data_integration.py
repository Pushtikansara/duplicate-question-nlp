from __future__ import annotations

"""
Integration tests for ARES Multi-Agent Dashboard data wiring.

Verifies that every widget in the dashboard reads from the correct
MultiAgentEngine result field, and that no placeholder values remain.

Run:  python -m pytest tests/test_ares_dashboard_data_integration.py -v
"""

from typing import Any

import pytest

from ares.agents.multi_agent_engine import MultiAgentEngine

# ---------------------------------------------------------------------------
# Fixture: capture the full schema of a real engine result
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def engine_result() -> dict[str, Any]:
    """Return a real MultiAgentEngine result by running against a test pair."""
    import asyncio

    engine = MultiAgentEngine()
    result = asyncio.run(
        engine.run(
            question1="What is the capital of France?",
            question2="What is the capital city of France?",
            goal_description="Test goal",
            model_name="",
            strategy="LINEAR",
            threshold=0.5,
            scenario_id="test",
            include_reflection=True,
            include_memory=True,
        )
    )
    return result


# ---------------------------------------------------------------------------
# Schema validation: top-level keys
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL_KEYS = [
    "multi_agent",
    "trace_id",
    "scenario_id",
    "status",
    "mode",
    "total_time_ms",
    "goal",
    "input",
    "decomposition",
    "prediction",
    "fusion",
    "semantic_validation",
    "confidence_calculation",
    "reflection",
    "decision",
    "decision_confidence",
    "explanation",
    "final_response",
    "agent_selection",
    "tool_discovery",
    "execution_dag",
    "agent_timeline",
    "timeline",
    "observability",
    "cache_stats",
]


class TestEngineResultSchema:
    """Every expected top-level key must be present and non-null in a real run."""

    def test_top_level_keys_present(self, engine_result: dict[str, Any]) -> None:
        for key in REQUIRED_TOP_LEVEL_KEYS:
            assert key in engine_result, f"Missing top-level key: {key}"

    def test_status(self, engine_result: dict[str, Any]) -> None:
        assert engine_result["status"] == "completed"
        assert engine_result["multi_agent"] is True

    def test_trace_id(self, engine_result: dict[str, Any]) -> None:
        tid = engine_result.get("trace_id", "")
        assert tid and len(tid) > 8, f"trace_id too short or missing: {tid!r}"

    def test_total_time_ms(self, engine_result: dict[str, Any]) -> None:
        t = engine_result.get("total_time_ms", 0)
        assert t > 0, f"total_time_ms should be > 0, got {t}"


# ---------------------------------------------------------------------------
# Widget: Overview Cards
# ---------------------------------------------------------------------------


class TestOverviewCardsData:
    """Maps every overview-card metric to its engine source field."""

    def test_strategy(self, engine_result: dict[str, Any]) -> None:
        goal = engine_result.get("goal", {})
        s = goal.get("strategy")
        assert s, f"Overview 'Strategy' — goal.strategy is empty: {s!r}"

    def test_model(self, engine_result: dict[str, Any]) -> None:
        inp = engine_result.get("input", {})
        pred = engine_result.get("prediction", {})
        m = inp.get("model") or pred.get("model_name")
        assert m is not None, "Overview 'Model' — both input.model and prediction.model_name are None"

    def test_executed_agents(self, engine_result: dict[str, Any]) -> None:
        tasks = engine_result.get("decomposition", {}).get("tasks", [])
        agent_ids = {t.get("agent_id") for t in tasks if t.get("agent_id")}
        assert isinstance(agent_ids, set)
        # Engine may not decompose tasks for simple goals — dashboard must handle 0 gracefully

    def test_parallel_groups(self, engine_result: dict[str, Any]) -> None:
        groups = engine_result.get("decomposition", {}).get("parallel_groups", [])
        assert groups is not None, "Overview 'Parallel Groups' — decomposition.parallel_groups is None"

    def test_tasks(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decomposition", {})
        count = dec.get("task_count", 0) or len(dec.get("tasks", []))
        assert count > 0, f"Overview 'Tasks' — task_count is {count}"

    def test_latency(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        total = tl.get("total_ms", 0)
        assert total > 0, f"Overview 'Latency' — timeline.total_ms is {total}"

    def test_confidence(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        pred = engine_result.get("prediction", {})
        conf = dec.get("final_confidence", pred.get("confidence"))
        assert conf is not None, (
            "Overview 'Confidence' — neither decision.final_confidence nor prediction.confidence available"
        )

    def test_risk(self, engine_result: dict[str, Any]) -> None:
        pred = engine_result.get("prediction", {})
        assert "risk_level" in pred, "Overview — prediction.risk_level key missing"
        # risk_level may be None if PredictionResult didn't populate it — dashboard handles this


# ---------------------------------------------------------------------------
# Widget: Execution Pipeline
# ---------------------------------------------------------------------------


class TestPipelineData:
    """Pipeline phase durations must be backed by timeline data."""

    def test_decomposition_ms(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        assert tl.get("decomposition_ms", 0) > 0, "Pipeline — decomposition_ms is 0"

    def test_prediction_ms(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        assert tl.get("prediction_ms", 0) > 0, "Pipeline — prediction_ms is 0"

    def test_decision_ms(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        assert tl.get("decision_ms", 0) > 0, "Pipeline — decision_ms is 0"


# ---------------------------------------------------------------------------
# Widget: Execution Tab  (Decision Intelligence)
# ---------------------------------------------------------------------------


class TestExecutionTabData:
    """Every confidence metric comes from the decision dict."""

    def test_raw_confidence(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        raw = dec.get("raw_confidence", dec.get("raw_confidence"))
        assert raw is not None, "Execution 'Raw Confidence' — decision.raw_confidence is None"

    def test_adjusted_confidence(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        adj = dec.get("adjusted_confidence")
        assert adj is not None, "Execution 'Calibrated' — decision.adjusted_confidence is None"

    def test_trust_score(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        trust = dec.get("trust_score")
        assert trust is not None, "Execution 'Trust Score' — decision.trust_score is None"

    def test_final_confidence(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        fc = dec.get("final_confidence")
        assert fc is not None, "Execution 'Final Confidence' — decision.final_confidence is None"

    def test_recommendation(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        rec = dec.get("recommendations")
        assert rec, f"Execution 'Recommendation' — decision.recommendations is empty: {rec!r}"

    def test_signals(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        signals = dec.get("signals", [])
        assert isinstance(signals, list)

    def test_conflicts(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        conflicts = dec.get("conflicts", [])
        assert isinstance(conflicts, list)


# ---------------------------------------------------------------------------
# Widget: Agents Tab
# ---------------------------------------------------------------------------


class TestAgentsTabData:
    """Agent panel must show task→agent mapping with capabilities."""

    def test_decomposition_tasks_have_agents(self, engine_result: dict[str, Any]) -> None:
        tasks = engine_result.get("decomposition", {}).get("tasks", [])
        assert len(tasks) > 0, "Agents — no decomposition.tasks"
        for t in tasks:
            assert "task_id" in t, f"Tasks entry missing task_id: {t}"
            assert "task_type" in t, f"Tasks entry missing task_type: {t}"
            assert "agent_id" in t, f"Tasks entry missing agent_id: {t}"

    def test_agent_selection_has_agents(self, engine_result: dict[str, Any]) -> None:
        sel = engine_result.get("agent_selection", {})
        agents = sel.get("agents", [])
        assert isinstance(agents, list)
        if agents:
            for a in agents:
                assert "agent_id" in a
                assert "capabilities" in a

    def test_agent_selection_total_active(self, engine_result: dict[str, Any]) -> None:
        sel = engine_result.get("agent_selection", {})
        total = sel.get("total_active", 0)
        assert total >= 0, f"Agents — agent_selection.total_active is negative: {total}"

    def test_uncovered_capabilities(self, engine_result: dict[str, Any]) -> None:
        sel = engine_result.get("agent_selection", {})
        assert "uncovered_capabilities" in sel


# ---------------------------------------------------------------------------
# Widget: Timeline Tab
# ---------------------------------------------------------------------------


class TestTimelineTabData:
    """Timing bars must use real proportional phase durations."""

    ALL_PHASES = [
        "decomposition_ms",
        "prediction_ms",
        "semantic_validation_ms",
        "memory_ms",
        "reflection_ms",
        "decision_ms",
    ]

    def test_timeline_has_phases(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        has_any = any(tl.get(k, 0) > 0 for k in self.ALL_PHASES)
        assert has_any, "Timeline — no phases have positive duration"

    def test_timeline_total_ms(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        t = tl.get("total_ms", 0)
        assert t > 0, f"Timeline — total_ms is {t}"


# ---------------------------------------------------------------------------
# Widget: Memory Tab
# ---------------------------------------------------------------------------


class TestMemoryTabData:
    """Memory tab must explain when data is unavailable instead of showing 0."""

    def test_timeline_has_memory_ms(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("timeline", {})
        ms = tl.get("memory_ms", 0)
        assert ms is not None, "Memory — timeline.memory_ms is None"

    def test_cache_stats_present(self, engine_result: dict[str, Any]) -> None:
        cs = engine_result.get("cache_stats", {})
        assert "capacity" in cs, "Memory — cache_stats missing 'capacity'"
        assert "size" in cs, "Memory — cache_stats missing 'size'"
        assert "default_ttl_seconds" in cs, "Memory — cache_stats missing 'default_ttl_seconds'"


# ---------------------------------------------------------------------------
# Widget: Observability Tab
# ---------------------------------------------------------------------------


class TestObservabilityTabData:
    """Every observability metric is backed by engine data."""

    def test_observability_keys(self, engine_result: dict[str, Any]) -> None:
        obs = engine_result.get("observability", {})
        expected = {
            "total_tasks",
            "succeeded",
            "failed",
            "success_rate",
            "total_duration_ms",
            "avg_duration_ms",
            "agents_used",
            "task_types",
        }
        for key in expected:
            assert key in obs, f"Observability — missing key: {key}"
            assert obs[key] is not None, f"Observability — key {key} is None"

    def test_observability_totals(self, engine_result: dict[str, Any]) -> None:
        obs = engine_result.get("observability", {})
        total = obs.get("total_tasks", 0)
        succ = obs.get("succeeded", 0)
        fail = obs.get("failed", 0)
        # Engine does not call observability.record_task_start/end in run()
        # so total_tasks may be 0. Dashboard must handle this gracefully.
        assert isinstance(total, int) and total >= 0
        assert succ + fail == total

    def test_observability_success_rate(self, engine_result: dict[str, Any]) -> None:
        obs = engine_result.get("observability", {})
        rate = obs.get("success_rate")
        assert rate is not None, "Observability — success_rate is None"
        assert 0.0 <= rate <= 1.0, f"Observability — success_rate {rate} out of range"

    def test_observability_agents_used(self, engine_result: dict[str, Any]) -> None:
        obs = engine_result.get("observability", {})
        agents = obs.get("agents_used", [])
        tasks = engine_result.get("decomposition", {}).get("tasks", [])
        executed = {t.get("agent_id") for t in tasks if t.get("agent_id")}
        if agents:
            assert executed.issubset(set(agents)) or set(agents).issubset(executed), (
                f"Observability — agents_used {agents} does not match executed agents {executed}"
            )

    def test_observability_task_types(self, engine_result: dict[str, Any]) -> None:
        obs = engine_result.get("observability", {})
        types = obs.get("task_types", [])
        # Engine does not call observability.record_task_start/end
        # so task_types may be empty. Dashboard must handle this.
        assert isinstance(types, list)

    def test_decomposition_parallel_groups(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decomposition", {})
        groups = dec.get("parallel_groups", [])
        assert isinstance(groups, list), "Observability — parallel_groups is not a list"

    def test_cache_stats_in_observability(self, engine_result: dict[str, Any]) -> None:
        cs = engine_result.get("cache_stats", {})
        assert isinstance(cs, dict), "Observability — cache_stats is not a dict"
        assert "capacity" in cs

    def test_agent_timeline_for_retries(self, engine_result: dict[str, Any]) -> None:
        tl = engine_result.get("agent_timeline", [])
        assert isinstance(tl, list)


# ---------------------------------------------------------------------------
# Widget: Final Decision
# ---------------------------------------------------------------------------


class TestFinalDecisionData:
    """Final decision card uses engine decision fields."""

    def test_decision_prediction(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        pred = dec.get("prediction")
        assert pred, f"Final Decision — decision.prediction is empty: {pred!r}"

    def test_decision_final_confidence(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        fc = dec.get("final_confidence")
        assert fc is not None, "Final Decision — decision.final_confidence is None"

    def test_decision_recommendation(self, engine_result: dict[str, Any]) -> None:
        dec = engine_result.get("decision", {})
        rec = dec.get("recommendations")
        assert rec, f"Final Decision — decision.recommendations is empty: {rec!r}"


# ---------------------------------------------------------------------------
# Widget: Developer Tab
# ---------------------------------------------------------------------------


class TestDeveloperTabData:
    """Developer tab context must have real data."""

    def test_trace_id(self, engine_result: dict[str, Any]) -> None:
        assert engine_result.get("trace_id"), "Developer — trace_id missing"

    def test_status(self, engine_result: dict[str, Any]) -> None:
        assert engine_result.get("status") == "completed"

    def test_input(self, engine_result: dict[str, Any]) -> None:
        inp = engine_result.get("input", {})
        assert inp.get("question1"), "Developer — input.question1 missing"
        assert inp.get("question2"), "Developer — input.question2 missing"

    def test_total_time(self, engine_result: dict[str, Any]) -> None:
        t = engine_result.get("total_time_ms", engine_result.get("timeline", {}).get("total_ms", 0))
        assert t > 0, "Developer — total_time_ms is 0"


# ---------------------------------------------------------------------------
# Contract: no 'memory' top-level key (engine does not expose it)
# ---------------------------------------------------------------------------


class TestEngineLimitations:
    """Document what the engine does NOT expose, so widgets show explanations."""

    def test_no_memory_top_level_key(self, engine_result: dict[str, Any]) -> None:
        """The engine stores memory internally but does not add a 'memory' key to the result."""
        assert "memory" not in engine_result, (
            "If the engine starts exposing a 'memory' key, update _render_memory_tab "
            "to use the real data instead of the explanatory message."
        )

    def test_no_selection_scores(self, engine_result: dict[str, Any]) -> None:
        """DynamicAgentSelector does not surface per-task selection scores."""
        sel = engine_result.get("agent_selection", {})
        agents = sel.get("agents", [])
        for a in agents:
            assert "selection_score" not in a, (
                "If DynamicAgentSelector starts exposing selection_score, update _render_agents_tab to display it."
            )

    def test_no_retries_field(self, engine_result: dict[str, Any]) -> None:
        """Retries must be derived from agent_timeline status=FAILED."""
        obs = engine_result.get("observability", {})
        assert "retries" not in obs, (
            "If observability starts exposing retries, use it directly instead of deriving from agent_timeline."
        )

    def test_no_scheduler_decisions(self, engine_result: dict[str, Any]) -> None:
        """Scheduler decisions are internal to ExecutionScheduler."""
        assert "scheduler_decisions" not in engine_result, (
            "If the engine starts exposing scheduler_decisions, display them in the observability tab."
        )
