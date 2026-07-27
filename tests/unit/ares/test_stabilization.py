from __future__ import annotations

import pytest

from ares.confidence import _consistent_reflection_from_confidence, _ensure_consistent_reflection
from ares.memory.store import MemoryStore
from ares.memory.types import MemoryTier
from ares.metrics import MetricsRegistry
from ares.orchestration.strategy import resolve_orchestration_strategy, resolve_planning_strategy
from ares.planning.graph import PlanGraph
from ares.planning.optimizer import PlanOptimizer
from ares.planning.types import Plan, PlanEdge, PlanningStrategy, PlanNode


class TestReflectionConsistency:
    def test_high_trust_low_risk(self) -> None:
        result = _consistent_reflection_from_confidence(0.96)
        assert result["trust_level"] == "HIGH"
        assert result["risk_level"] == "LOW"
        assert result["human_review_required"] is False

    def test_medium_trust_medium_risk(self) -> None:
        result = _consistent_reflection_from_confidence(0.70)
        assert result["trust_level"] == "MEDIUM"
        assert result["risk_level"] == "MEDIUM"
        assert result["human_review_required"] is False

    def test_low_trust_high_risk(self) -> None:
        result = _consistent_reflection_from_confidence(0.50)
        assert result["trust_level"] == "LOW"
        assert result["risk_level"] == "HIGH"
        assert result["human_review_required"] is True

    def test_boundary_95(self) -> None:
        result = _consistent_reflection_from_confidence(0.95)
        assert result["trust_level"] == "HIGH"

    def test_boundary_70(self) -> None:
        result = _consistent_reflection_from_confidence(0.70)
        assert result["trust_level"] == "MEDIUM"

    def test_ensure_consistent_overrides(self) -> None:
        result = _ensure_consistent_reflection(
            {
                "trust_score": 0.96,
                "trust_level": "LOW",
                "risk_level": "HIGH",
                "human_review_required": True,
                "recommendations": [],
            }
        )
        assert result["trust_level"] == "HIGH"
        assert result["risk_level"] == "LOW"
        assert result["human_review_required"] is False

    def test_ensure_consistent_preserves_recommendations(self) -> None:
        result = _ensure_consistent_reflection(
            {
                "trust_score": 0.50,
                "trust_level": "HIGH",
                "risk_level": "LOW",
                "human_review_required": False,
                "recommendations": ["review_manually"],
            }
        )
        assert result["trust_level"] == "LOW"
        assert result["risk_level"] == "HIGH"
        assert result["human_review_required"] is True

    def test_recommendations_generated_dynamically_high(self) -> None:
        result = _consistent_reflection_from_confidence(0.96)
        assert result["recommendations"] == []

    def test_recommendations_generated_dynamically_medium(self) -> None:
        result = _consistent_reflection_from_confidence(0.80)
        assert result["recommendations"] == []

    def test_recommendations_generated_dynamically_low(self) -> None:
        result = _consistent_reflection_from_confidence(0.50)
        assert "review_manually" in result["recommendations"]

    def test_recommendations_generated_dynamically_very_low(self) -> None:
        result = _consistent_reflection_from_confidence(0.20)
        assert "review_manually" in result["recommendations"]
        assert "flag_for_expert_review" in result["recommendations"]


class TestGraphValidator:
    def test_detects_self_loop(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n1"))
        graph = PlanGraph(plan)
        errors = GraphValidator().validate(graph)
        assert any("self-loop" in e.lower() for e in errors)

    def test_detects_duplicate_edge(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        graph = PlanGraph(plan)
        errors = GraphValidator().validate(graph)
        assert any("duplicate" in e.lower() for e in errors)

    def test_detects_cycle(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_node(PlanNode(node_id="n3", goal_id="g1", agent_id="c", action="z"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        plan.add_edge(PlanEdge(source_id="n2", target_id="n3"))
        plan.add_edge(PlanEdge(source_id="n3", target_id="n1"))
        graph = PlanGraph(plan)
        errors = GraphValidator().validate(graph)
        assert any("cycle" in e.lower() for e in errors)

    def test_detects_missing_node(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1", strategy=PlanningStrategy.DAG)
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n3"))
        graph = PlanGraph(plan)
        errors = GraphValidator().validate(graph)
        missing = [e for e in errors if "not a node" in e.lower()]
        assert missing, f"No missing node error found: {errors}"

    def test_valid_linear_passes(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1", strategy=PlanningStrategy.LINEAR)
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_node(PlanNode(node_id="n3", goal_id="g1", agent_id="c", action="z"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        plan.add_edge(PlanEdge(source_id="n2", target_id="n3"))
        graph = PlanGraph(plan)
        errors = GraphValidator().validate(graph)
        dag_errors = [
            e for e in errors if "cycle" in e.lower() or "unreachable" in e.lower() or "self-loop" in e.lower()
        ]
        assert len(dag_errors) == 0

    def test_is_dag_true(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        graph = PlanGraph(plan)
        assert GraphValidator().is_dag(graph)

    def test_is_dag_false(self) -> None:
        from ares.planning.validator import GraphValidator

        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="b", action="y"))
        plan.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        plan.add_edge(PlanEdge(source_id="n2", target_id="n1"))
        graph = PlanGraph(plan)
        assert not GraphValidator().is_dag(graph)


class TestSemanticValidation:
    def test_no_ambiguity(self) -> None:
        from ares.semantic_validator import validate_semantic

        class FakeResult:
            confidence = 0.95

        result = validate_semantic("What is the capital of France", "What is the capital of Italy", FakeResult())
        assert not result["ambiguity_detected"]

    def test_detects_contradiction(self) -> None:
        from ares.semantic_validator import validate_semantic

        class FakeResult:
            confidence = 0.95

        result = validate_semantic("I love programming", "I hate programming", FakeResult())
        assert result["ambiguity_detected"]
        assert result["semantic_detail"]["contradiction_count"] > 0

    def test_detects_negation(self) -> None:
        from ares.semantic_validator import validate_semantic

        class FakeResult:
            confidence = 0.90

        result = validate_semantic("This is not good", "This is good", FakeResult())
        assert result["ambiguity_detected"]

    def test_confidence_reduced_by_contradiction(self) -> None:
        from ares.semantic_validator import validate_semantic

        class FakeResult:
            confidence = 0.95

        result = validate_semantic("I love programming", "I hate programming", FakeResult())
        assert result["adjusted_confidence"] < 0.95

    def test_no_ambiguity_for_low_confidence(self) -> None:
        from ares.semantic_validator import validate_semantic

        class FakeResult:
            confidence = 0.50

        result = validate_semantic("How to fix a broken pipe", "What is the tallest mountain", FakeResult())
        assert not result["ambiguity_detected"]


class TestCalibration:
    def test_calibrate_classical_ml(self) -> None:
        from ares.inference.calibration import calibrate_score

        report = calibrate_score(0.80, "classical-lr", threshold=0.5)
        assert report.calibrated_score < report.raw_score
        assert report.calibration_quality in ("well_calibrated", "acceptable")

    def test_calibrate_transformer(self) -> None:
        from ares.inference.calibration import calibrate_score

        report = calibrate_score(0.80, "transformer-bert", threshold=0.5)
        assert report.calibrated_score < report.raw_score

    def test_overconfidence_detected(self) -> None:
        from ares.inference.calibration import calibrate_score

        report = calibrate_score(0.99, "classical-lr", threshold=0.5)
        assert report.calibrated_score != report.raw_score
        assert report.calibration_quality in ("well_calibrated", "acceptable", "needs_calibration")

    def test_calibrate_ensemble(self) -> None:
        from ares.inference.calibration import calibrate_score

        report = calibrate_score(0.80, "ensemble-xgboost", threshold=0.5)
        assert report.decision in ("duplicate", "non_duplicate")
        assert report.model_name == "ensemble-xgboost"


class TestMemoryStoreCapacity:
    def test_default_capacities(self) -> None:
        store = MemoryStore()
        assert store._tier_capacities[MemoryTier.WORKING] == 500
        assert store._tier_capacities[MemoryTier.SHORT_TERM] == 1000
        assert store._tier_capacities[MemoryTier.LONG_TERM] == 5000

    def test_custom_capacity(self) -> None:
        store = MemoryStore(tier_capacities={MemoryTier.WORKING: 10})
        assert store._tier_capacities[MemoryTier.WORKING] == 10
        assert store._tier_capacities[MemoryTier.SHORT_TERM] == 1000

    def test_fifo_eviction(self) -> None:
        store = MemoryStore(tier_capacities={MemoryTier.WORKING: 3})
        for i in range(5):
            store.store(key=f"k{i}", value=i, tier=MemoryTier.WORKING)
        assert len(store._in_memory) <= 3
        assert store.eviction_count == 2

    def test_no_eviction_below_capacity(self) -> None:
        store = MemoryStore(tier_capacities={MemoryTier.WORKING: 10})
        for i in range(5):
            store.store(key=f"k{i}", value=i, tier=MemoryTier.WORKING)
        assert store.eviction_count == 0

    def test_eviction_by_tier(self) -> None:
        store = MemoryStore(tier_capacities={MemoryTier.WORKING: 2, MemoryTier.LONG_TERM: 10})
        store.store(key="k1", value=1, tier=MemoryTier.WORKING)
        store.store(key="k2", value=2, tier=MemoryTier.WORKING)
        store.store(key="k3", value=3, tier=MemoryTier.WORKING)
        assert store.eviction_count == 1
        store.store(key="lk1", value=1, tier=MemoryTier.LONG_TERM)
        store.store(key="lk2", value=2, tier=MemoryTier.LONG_TERM)
        assert store.eviction_count == 1

    def test_sweep_expired(self) -> None:
        store = MemoryStore()
        store.store(key="persist", value="keep", tier=MemoryTier.WORKING)
        store.store(key="expire", value="gone", tier=MemoryTier.WORKING, ttl_seconds=-1)
        swept = store.sweep_expired()
        assert swept == 1
        assert "expire" not in {e.key for e in store._in_memory.values()}

    def test_stats_includes_evictions(self) -> None:
        store = MemoryStore(tier_capacities={MemoryTier.WORKING: 1})
        store.store(key="k1", value=1, tier=MemoryTier.WORKING)
        store.store(key="k2", value=2, tier=MemoryTier.WORKING)
        stats = store.get_stats()
        assert stats.eviction_count == 1


class TestMetricsRegistry:
    def test_singleton(self) -> None:
        r1 = MetricsRegistry()
        r2 = MetricsRegistry()
        assert r1 is r2

    def test_increment(self) -> None:
        MetricsRegistry().reset()
        MetricsRegistry().increment("test.counter")
        assert MetricsRegistry().counter("test.counter") == 1
        MetricsRegistry().increment("test.counter", amount=5)
        assert MetricsRegistry().counter("test.counter") == 6

    def test_gauge(self) -> None:
        MetricsRegistry().reset()
        MetricsRegistry().gauge("test.gauge", 42.0)
        snapshot = MetricsRegistry().snapshot()
        assert snapshot["gauges"]["test.gauge"] == 42.0

    def test_snapshot(self) -> None:
        MetricsRegistry().reset()
        MetricsRegistry().increment("a")
        MetricsRegistry().gauge("b", 1.0)
        snap = MetricsRegistry().snapshot()
        assert snap["counters"]["a"] == 1
        assert snap["gauges"]["b"] == 1.0

    def test_reset(self) -> None:
        MetricsRegistry().reset()
        MetricsRegistry().increment("x")
        MetricsRegistry().reset()
        snap = MetricsRegistry().snapshot()
        assert snap["counters"] == {}


class TestStrategyEnforcer:
    def test_resolve_planning_linear(self) -> None:
        assert resolve_planning_strategy("LINEAR") == PlanningStrategy.LINEAR

    def test_resolve_planning_case_insensitive(self) -> None:
        assert resolve_planning_strategy("linear") == PlanningStrategy.LINEAR

    def test_resolve_planning_unknown_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown planning strategy"):
            resolve_planning_strategy("unknown_strat")

    def test_resolve_planning_none_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="No planning strategy provided"):
            resolve_planning_strategy(None)

    def test_resolve_orchestration_sequential(self) -> None:
        from ares.orchestration.types import OrchestrationStrategyType

        assert resolve_orchestration_strategy("SEQUENTIAL") == OrchestrationStrategyType.SEQUENTIAL

    def test_resolve_orchestration_unknown_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown orchestration strategy"):
            resolve_orchestration_strategy("bogus")


class TestOptimizerDedup:
    def test_deduplicate_same_agent_action(self) -> None:
        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="planner", action="create_plan"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="planner", action="create_plan"))
        graph = PlanGraph(plan)
        opt = PlanOptimizer()
        removed = opt._deduplicate_nodes(graph)
        assert removed == 1
        assert len(graph.plan.nodes) == 1

    def test_deduplicate_preserves_unique(self) -> None:
        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="planner", action="create_plan"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="predict", action="predict"))
        graph = PlanGraph(plan)
        opt = PlanOptimizer()
        removed = opt._deduplicate_nodes(graph)
        assert removed == 0
        assert len(graph.plan.nodes) == 2

    def test_deduplicate_rewires_edges(self) -> None:
        plan = Plan(plan_id="p1", goal_id="g1")
        plan.add_node(PlanNode(node_id="n1", goal_id="g1", agent_id="predict", action="predict"))
        plan.add_node(PlanNode(node_id="n2", goal_id="g1", agent_id="predict", action="predict"))
        plan.add_node(PlanNode(node_id="n3", goal_id="g1", agent_id="reflect", action="reflect"))
        plan.add_edge(PlanEdge(source_id="n2", target_id="n3"))
        graph = PlanGraph(plan)
        opt = PlanOptimizer()
        removed = opt._deduplicate_nodes(graph)
        assert removed == 1
        assert len(graph.plan.edges) <= 1


class TestStrategyPropagation:
    @pytest.mark.parametrize("strategy_name", ["LINEAR", "TREE", "DAG", "GRAPH", "HIERARCHICAL", "AUTO"])
    def test_each_strategy_produces_correct_graph(self, strategy_name: str) -> None:
        from ares.orchestration.strategy import resolve_planning_strategy
        from ares.planning.engine import PlanningEngine

        strategy_enum = resolve_planning_strategy(strategy_name)
        assert strategy_enum.name == strategy_name, f"Resolver mismatch: '{strategy_name}' → '{strategy_enum.name}'"
        engine = PlanningEngine()
        goal = engine.create_goal("Test goal", decompose=False)
        graph = engine.create_plan(goal, strategy=strategy_enum)
        assert graph.plan.strategy.name == strategy_name, (
            f"Planner mismatch: resolver gave '{strategy_enum.name}' but graph has '{graph.plan.strategy.name}'"
        )

    @pytest.mark.parametrize("strategy_name", ["LINEAR", "TREE", "DAG", "GRAPH", "HIERARCHICAL", "AUTO"])
    def test_each_strategy_assertion_passes(self, strategy_name: str) -> None:
        from ares.orchestration.strategy import resolve_planning_strategy
        from ares.planning.engine import PlanningEngine

        strategy_enum = resolve_planning_strategy(strategy_name)
        assert strategy_enum.name == strategy_name.upper()
        engine = PlanningEngine()
        goal = engine.create_goal("Test goal assertion", decompose=False)
        graph = engine.create_plan(goal, strategy=strategy_enum)
        assert graph.plan.strategy == strategy_enum

    def test_ui_mock_propagates_to_demo_engine(self) -> None:
        import asyncio

        from ares.demo_engine import DemoEngine

        engine = DemoEngine()
        engine.initialize()
        for strategy_name in ["LINEAR", "TREE", "DAG", "GRAPH", "HIERARCHICAL", "AUTO"]:
            result = asyncio.run(
                engine.run_demo(
                    question1="What is Python?",
                    question2="What is Java?",
                    strategy=strategy_name,
                    goal="Test strategy propagation",
                )
            )
            assert result["strategy"]["requested"] == strategy_name, (
                f"Requested '{strategy_name}' but result shows '{result['strategy']['requested']}'"
            )
            assert result["strategy"]["resolved"] == strategy_name, (
                f"Resolved '{strategy_name}' but result shows '{result['strategy']['resolved']}'"
            )
            assert result["plan"]["strategy"] == strategy_name, (
                f"Graph shows '{result['plan']['strategy']}' instead of '{strategy_name}'"
            )
