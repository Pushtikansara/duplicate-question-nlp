from __future__ import annotations

from ares.planning import PlanningStrategy, PlanNodeStatus


class TestPlanner:
    def test_linear_plan(self, planner, sample_goal, agent_ids) -> None:
        graph = planner.plan(sample_goal, PlanningStrategy.LINEAR, agent_ids)
        assert graph.plan.strategy == PlanningStrategy.LINEAR
        assert len(graph.plan.nodes) >= 1

    def test_tree_plan(self, planner, decomposed_goal, agent_ids) -> None:
        graph = planner.plan(decomposed_goal, PlanningStrategy.TREE, agent_ids)
        assert graph.plan.strategy == PlanningStrategy.TREE
        assert len(graph.plan.nodes) >= 3

    def test_dag_plan(self, planner, sample_goal, agent_ids) -> None:
        graph = planner.plan(sample_goal, PlanningStrategy.DAG, agent_ids)
        assert graph.plan.strategy == PlanningStrategy.DAG
        assert len(graph.plan.nodes) >= 1

    def test_hierarchical_plan(self, planner, decomposed_goal, agent_ids) -> None:
        graph = planner.plan(decomposed_goal, PlanningStrategy.HIERARCHICAL, agent_ids)
        assert graph.plan.strategy == PlanningStrategy.HIERARCHICAL
        assert len(graph.plan.nodes) >= 1

    def test_reactive_plan(self, planner, sample_goal, agent_ids) -> None:
        graph = planner.plan(sample_goal, PlanningStrategy.REACTIVE, agent_ids)
        assert graph.plan.strategy == PlanningStrategy.REACTIVE
        assert len(graph.plan.nodes) >= 1

    def test_decompose_goal_simple(self, planner) -> None:
        goal = planner.decompose_goal("Do task A and Do task B")
        assert len(goal.sub_goals) > 0

    def test_decompose_goal_no_split(self, planner) -> None:
        goal = planner.decompose_goal("Just a single task")
        assert len(goal.sub_goals) >= 4

    def test_replan(self, planner, sample_graph, agent_ids) -> None:
        n2 = sample_graph.get_node("n2")
        n2.status = PlanNodeStatus.FAILED
        n1 = sample_graph.get_node("n1")
        n1.status = PlanNodeStatus.COMPLETED
        new_graph = planner.replan(sample_graph.plan, "n2", agent_ids)
        assert new_graph is not None
        assert len(new_graph.plan.nodes) >= 1
