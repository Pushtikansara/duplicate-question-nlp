from __future__ import annotations

import pytest

from ares.planning import PlanEdge, PlanGraph, PlanNode
from ares.planning.exceptions import CircularDependencyError, DuplicateNodeError


class TestPlanGraph:
    def test_add_node(self, sample_graph: PlanGraph) -> None:
        assert len(sample_graph.plan.nodes) == 3

    def test_add_duplicate_node(self, sample_graph: PlanGraph) -> None:
        n = PlanNode(node_id="n1", goal_id="g1", agent_id="a", action="x")
        with pytest.raises(DuplicateNodeError):
            sample_graph.add_node(n)

    def test_add_edge(self, sample_graph: PlanGraph) -> None:
        order = sample_graph.get_execution_order()
        assert len(order) >= 1

    def test_cycle_detection(self, sample_graph: PlanGraph) -> None:
        with pytest.raises(CircularDependencyError):
            sample_graph.add_edge(PlanEdge(source_id="n3", target_id="n1"))

    def test_get_node(self, sample_graph: PlanGraph) -> None:
        node = sample_graph.get_node("n1")
        assert node.node_id == "n1"

    def test_get_ready_nodes(self, sample_graph: PlanGraph) -> None:
        ready = sample_graph.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].node_id == "n1"

    def test_get_roots(self, sample_graph: PlanGraph) -> None:
        roots = sample_graph.get_roots()
        assert any(n.node_id == "n1" for n in roots)

    def test_get_leaves(self, sample_graph: PlanGraph) -> None:
        leaves = sample_graph.get_leaves()
        assert any(n.node_id == "n3" for n in leaves)

    def test_get_dependents(self, sample_graph: PlanGraph) -> None:
        deps = sample_graph.get_dependents("n1")
        assert any(n.node_id == "n2" for n in deps)

    def test_get_dependencies(self, sample_graph: PlanGraph) -> None:
        deps = sample_graph.get_dependencies("n2")
        assert any(n.node_id == "n1" for n in deps)

    def test_get_levels(self, sample_graph: PlanGraph) -> None:
        levels = sample_graph.get_levels()
        assert len(levels) >= 1

    def test_validate_structure_valid(self, sample_graph: PlanGraph) -> None:
        errors = sample_graph.validate_structure()
        assert len(errors) == 0

    def test_validate_structure_missing_dep(self, sample_graph: PlanGraph) -> None:
        n = PlanNode(node_id="n4", goal_id="g1", agent_id="a", action="x", depends_on=["n99"])
        sample_graph.add_node(n)
        errors = sample_graph.validate_structure()
        assert any("n99" in e for e in errors)

    def test_get_complexity(self, sample_graph: PlanGraph) -> None:
        c = sample_graph.get_complexity()
        assert c["nodes"] == 3
        assert c["edges"] == 2

    def test_to_dict(self, sample_graph: PlanGraph) -> None:
        d = sample_graph.to_dict()
        assert d["plan_id"] == "plan-1"
        assert "nodes" in d
        assert "edges" in d
        assert "execution_order" in d
