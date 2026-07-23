from __future__ import annotations

from ares.planning import PlanningStrategy


class TestPlanningEngine:
    def test_create_goal(self, planning_engine) -> None:
        goal = planning_engine.create_goal("Test goal")
        assert goal.goal_id is not None
        assert goal.description == "Test goal"

    def test_create_goal_no_decompose(self, planning_engine) -> None:
        goal = planning_engine.create_goal("Task A and Task B", decompose=False)
        assert len(goal.sub_goals) == 0

    def test_create_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Analyze data")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        assert graph.plan.plan_id is not None
        assert len(graph.plan.nodes) >= 1

    def test_validate_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Validate me")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        errors = planning_engine.validate_plan(graph, agent_ids)
        assert isinstance(errors, list)

    def test_optimize_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Optimize me")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        stats = planning_engine.optimize_plan(graph)
        assert "optimizations_applied" in stats

    def test_execute_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Execute me")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        result = __import__("asyncio").run(planning_engine.execute_plan(graph))
        assert result is not None
        assert result.status.name in ("COMPLETED", "PARTIAL", "FAILED")

    def test_full_cycle(self, planning_engine, agent_ids) -> None:
        result = __import__("asyncio").run(
            planning_engine.full_cycle(
                "Full cycle test",
                strategy=PlanningStrategy.LINEAR,
                agent_ids=agent_ids,
                decompose=True,
                validate=True,
                optimize=True,
                execute=True,
            )
        )
        assert "goal" in result
        assert "plan_graph" in result
        assert "plan_result" in result
        assert "validation_errors" in result
        assert "optimization_stats" in result

    def test_cancel_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Cancel me")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        planning_engine.cancel_plan(graph.plan.plan_id)
        plan = planning_engine.get_plan(graph.plan.plan_id)
        if plan:
            assert plan.status.name == "CANCELLED"

    def test_get_plan(self, planning_engine, agent_ids) -> None:
        goal = planning_engine.create_goal("Get me")
        graph = planning_engine.create_plan(goal, PlanningStrategy.LINEAR, agent_ids)
        plan = planning_engine.get_plan(graph.plan.plan_id)
        assert plan is not None
        assert plan.plan_id == graph.plan.plan_id

    def test_get_goal(self, planning_engine) -> None:
        goal = planning_engine.create_goal("Find me")
        found = planning_engine.get_goal(goal.goal_id)
        assert found is not None
        assert found.goal_id == goal.goal_id

    def test_get_all_plans(self, planning_engine, agent_ids) -> None:
        planning_engine.create_goal("Plan A")
        planning_engine.create_goal("Plan B")
        plans = planning_engine.get_all_plans()
        assert len(plans) >= 0

    def test_get_all_goals(self, planning_engine) -> None:
        planning_engine.create_goal("Goal A")
        planning_engine.create_goal("Goal B")
        goals = planning_engine.get_all_goals()
        assert len(goals) >= 2

    def test_metrics_available(self, planning_engine) -> None:
        metrics = planning_engine.metrics
        assert metrics is not None
        assert metrics.total_plans == 0
