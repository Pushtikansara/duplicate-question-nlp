from __future__ import annotations

import pytest

from ares.planning import (
    Goal,
    Plan,
    PlanEdge,
    PlanExecutor,
    PlanGraph,
    Planner,
    PlanningEngine,
    PlanningMetrics,
    PlanningStrategy,
    PlanNode,
    PlanOptimizer,
    PlanValidator,
)


@pytest.fixture
def sample_goal() -> Goal:
    return Goal(goal_id="goal-1", description="Analyze customer feedback and generate report")


@pytest.fixture
def decomposed_goal() -> Goal:
    root = Goal(goal_id="root", description="Process data and generate insights")
    sg1 = Goal(goal_id="sg1", description="Collect data from sources")
    sg2 = Goal(goal_id="sg2", description="Clean and normalize data")
    sg3 = Goal(goal_id="sg3", description="Run analysis")
    sg3.add_sub_goal(Goal(goal_id="sg3a", description="Statistical analysis"))
    sg3.add_sub_goal(Goal(goal_id="sg3b", description="ML analysis"))
    root.add_sub_goal(sg1)
    root.add_sub_goal(sg2)
    root.add_sub_goal(sg3)
    return root


@pytest.fixture
def sample_plan() -> Plan:
    return Plan(plan_id="plan-1", goal_id="goal-1", strategy=PlanningStrategy.LINEAR)


@pytest.fixture
def sample_nodes() -> list[PlanNode]:
    return [
        PlanNode(node_id="n1", goal_id="goal-1", agent_id="agent-a", action="Fetch data"),
        PlanNode(node_id="n2", goal_id="goal-1", agent_id="agent-b", action="Process data", depends_on=["n1"]),
        PlanNode(node_id="n3", goal_id="goal-1", agent_id="agent-c", action="Generate report", depends_on=["n2"]),
    ]


@pytest.fixture
def sample_graph(sample_plan: Plan, sample_nodes: list[PlanNode]) -> PlanGraph:
    graph = PlanGraph(sample_plan)
    for node in sample_nodes:
        graph.add_node(node)
    for dep in [("n1", "n2"), ("n2", "n3")]:
        graph.add_edge(PlanEdge(source_id=dep[0], target_id=dep[1]))
    return graph


@pytest.fixture
def planner() -> Planner:
    return Planner()


@pytest.fixture
def validator() -> PlanValidator:
    return PlanValidator()


@pytest.fixture
def optimizer() -> PlanOptimizer:
    return PlanOptimizer()


@pytest.fixture
def executor() -> PlanExecutor:
    return PlanExecutor()


@pytest.fixture
def metrics() -> PlanningMetrics:
    return PlanningMetrics()


@pytest.fixture
def planning_engine() -> PlanningEngine:
    return PlanningEngine()


@pytest.fixture
def agent_ids() -> list[str]:
    return ["agent-a", "agent-b", "agent-c"]


@pytest.fixture
def tool_ids() -> list[str]:
    return ["tool-fetch", "tool-process", "tool-report"]
