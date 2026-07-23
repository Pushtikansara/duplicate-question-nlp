from __future__ import annotations

from ares.planning.types import (
    Goal,
    GoalStatus,
    Plan,
    PlanEdge,
    PlanningStrategy,
    PlanNode,
    PlanNodeStatus,
    PlanResult,
    PlanStatus,
)


class TestGoal:
    def test_create_goal(self) -> None:
        g = Goal(goal_id="g1", description="test")
        assert g.goal_id == "g1"
        assert g.status == GoalStatus.PENDING

    def test_add_sub_goal(self) -> None:
        parent = Goal(goal_id="p", description="parent")
        child = Goal(goal_id="c", description="child")
        parent.add_sub_goal(child)
        assert len(parent.sub_goals) == 1
        assert child.parent_goal_id == "p"


class TestPlanNode:
    def test_create_node(self) -> None:
        n = PlanNode(node_id="n1", goal_id="g1", agent_id="a1", action="do")
        assert n.status == PlanNodeStatus.PENDING
        assert n.retry_count == 0

    def test_node_dependencies(self) -> None:
        n = PlanNode(node_id="n2", goal_id="g1", agent_id="a1", action="do", depends_on=["n1"])
        assert "n1" in n.depends_on


class TestPlanEdge:
    def test_create_edge(self) -> None:
        e = PlanEdge(source_id="n1", target_id="n2")
        assert e.source_id == "n1"
        assert e.target_id == "n2"
        assert e.condition is None


class TestPlan:
    def test_create_plan(self) -> None:
        p = Plan(plan_id="p1", goal_id="g1")
        assert p.status == PlanStatus.DRAFT
        assert p.strategy == PlanningStrategy.LINEAR

    def test_add_node(self, sample_nodes) -> None:
        p = Plan(plan_id="p1", goal_id="g1")
        p.add_node(sample_nodes[0])
        assert "n1" in p.nodes

    def test_add_edge(self) -> None:
        p = Plan(plan_id="p1", goal_id="g1")
        p.add_edge(PlanEdge(source_id="n1", target_id="n2"))
        assert len(p.edges) == 1

    def test_get_ready_nodes(self, sample_graph) -> None:
        ready = sample_graph.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].node_id == "n1"

    def test_get_execution_order(self, sample_graph) -> None:
        order = sample_graph.get_execution_order()
        assert len(order) >= 1


class TestPlanResult:
    def test_create_result(self) -> None:
        r = PlanResult(plan_id="p1", goal_id="g1", status=PlanStatus.COMPLETED, node_results={})
        assert r.plan_id == "p1"
        assert r.status == PlanStatus.COMPLETED
