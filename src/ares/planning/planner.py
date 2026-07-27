from __future__ import annotations

import logging
import uuid

from ares.planning.exceptions import GoalDecompositionError
from ares.planning.graph import PlanGraph
from ares.planning.types import (
    Goal,
    Plan,
    PlanEdge,
    PlanningStrategy,
    PlanNode,
    PlanNodeStatus,
)

logger = logging.getLogger(__name__)


class Planner:
    _DEFAULT_STAGES = [
        "Load the selected model from the model registry",
        "Validate the input questions for length and content",
        "Generate prediction using the inference engine",
        "Store the prediction result in memory",
        "Run reflection to assess trust and confidence",
        "Build and return the final response",
    ]

    def plan(
        self,
        goal: Goal,
        strategy: PlanningStrategy = PlanningStrategy.LINEAR,
        agent_ids: list[str] | None = None,
        available_tools: list[str] | None = None,
    ) -> PlanGraph:
        if strategy == PlanningStrategy.LINEAR:
            return self._plan_linear(goal, agent_ids or [])
        elif strategy == PlanningStrategy.TREE:
            return self._plan_tree(goal, agent_ids or [])
        elif strategy == PlanningStrategy.DAG:
            return self._plan_dag(goal, agent_ids or [])
        elif strategy == PlanningStrategy.GRAPH:
            graph = self._plan_dag(goal, agent_ids or [])
            graph.plan.strategy = PlanningStrategy.GRAPH
            return graph
        elif strategy == PlanningStrategy.HIERARCHICAL:
            return self._plan_hierarchical(goal, agent_ids or [])
        elif strategy == PlanningStrategy.REACTIVE:
            return self._plan_reactive(goal, agent_ids or [])
        elif strategy == PlanningStrategy.AUTO:
            return self._plan_auto(goal, agent_ids or [])
        raise GoalDecompositionError(detail=f"Unknown strategy: {strategy}")

    def _plan_auto(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        stages = self._build_multi_stage_goal(goal)
        if len(stages) <= 3:
            graph = self._plan_linear(goal, agent_ids)
        elif len(stages) <= 5:
            graph = self._plan_tree(goal, agent_ids)
        else:
            graph = self._plan_dag(goal, agent_ids)
        graph.plan.strategy = PlanningStrategy.AUTO
        return graph

    def _plan_linear(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        plan = Plan(plan_id=str(uuid.uuid4()), goal_id=goal.goal_id, strategy=PlanningStrategy.LINEAR)
        graph = PlanGraph(plan)
        stages = self._build_multi_stage_goal(goal)
        previous_id: str | None = None
        for i, stage in enumerate(stages):
            aid = agent_ids[i % len(agent_ids)] if agent_ids else "default"
            node = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=aid,
                action=stage.description,
                depends_on=[previous_id] if previous_id else [],
                latency_estimate_ms=100.0 + (i * 50),
                cost_estimate=0.1 + (i * 0.05),
                metadata={"stage": i, "total_stages": len(stages)},
            )
            graph.add_node(node)
            if previous_id:
                graph.add_edge(PlanEdge(source_id=previous_id, target_id=node.node_id))
            previous_id = node.node_id
        return graph

    def _plan_tree(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        plan = Plan(plan_id=str(uuid.uuid4()), goal_id=goal.goal_id, strategy=PlanningStrategy.TREE)
        graph = PlanGraph(plan)
        stages = self._build_multi_stage_goal(goal)
        if not stages:
            return graph
        root = PlanNode(
            node_id=str(uuid.uuid4()),
            goal_id=goal.goal_id,
            agent_id=agent_ids[0 % len(agent_ids)] if agent_ids else "default",
            action=goal.description,
            latency_estimate_ms=50.0,
            cost_estimate=0.05,
            metadata={"stage": 0, "is_root": True, "total_stages": len(stages)},
        )
        graph.add_node(root)
        mid = len(stages) // 2
        left_branch = stages[:mid]
        right_branch = stages[mid:]
        left_leaf = self._build_branch(graph, left_branch, root.node_id, agent_ids, 1)
        right_leaf = self._build_branch(graph, right_branch, root.node_id, agent_ids, 1)
        if left_leaf and right_leaf:
            merge = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=goal.goal_id,
                agent_id=agent_ids[-1 % len(agent_ids)] if agent_ids else "default",
                action="Merge results from both branches",
                depends_on=[left_leaf, right_leaf],
                latency_estimate_ms=50.0,
                cost_estimate=0.05,
                metadata={"stage": len(stages), "is_merge": True},
            )
            graph.add_node(merge)
            graph.add_edge(PlanEdge(source_id=left_leaf, target_id=merge.node_id))
            graph.add_edge(PlanEdge(source_id=right_leaf, target_id=merge.node_id))
        return graph

    def _build_branch(
        self, graph: PlanGraph, stages: list[Goal], parent_id: str, agent_ids: list[str], start_idx: int
    ) -> str | None:
        prev_id = parent_id
        for i, stage in enumerate(stages):
            aid = agent_ids[(start_idx + i) % len(agent_ids)] if agent_ids else "default"
            node = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=aid,
                action=stage.description,
                depends_on=[prev_id],
                latency_estimate_ms=80.0 + (i * 30),
                cost_estimate=0.1,
                metadata={"stage": start_idx + i, "branch": "parallel"},
            )
            graph.add_node(node)
            graph.add_edge(PlanEdge(source_id=prev_id, target_id=node.node_id))
            prev_id = node.node_id
        return prev_id

    def _plan_dag(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        plan = Plan(plan_id=str(uuid.uuid4()), goal_id=goal.goal_id, strategy=PlanningStrategy.DAG)
        graph = PlanGraph(plan)
        stages = self._build_multi_stage_goal(goal)
        if not stages:
            return graph
        nodes: list[PlanNode] = []
        for i, stage in enumerate(stages):
            aid = agent_ids[i % len(agent_ids)] if agent_ids else "default"
            node = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=aid,
                action=stage.description,
                latency_estimate_ms=60.0 + (i * 20),
                cost_estimate=0.08,
                metadata={"stage": i},
            )
            graph.add_node(node)
            nodes.append(node)
        for i in range(1, len(nodes)):
            graph.add_edge(PlanEdge(source_id=nodes[i - 1].node_id, target_id=nodes[i].node_id))
        if len(nodes) > 2:
            graph.add_edge(
                PlanEdge(source_id=nodes[0].node_id, target_id=nodes[-1].node_id, condition="skip_intermediate")
            )
        return graph

    def _plan_hierarchical(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        plan = Plan(plan_id=str(uuid.uuid4()), goal_id=goal.goal_id, strategy=PlanningStrategy.HIERARCHICAL)
        graph = PlanGraph(plan)
        stages = self._build_multi_stage_goal(goal)
        if not stages:
            return graph
        coordinator = PlanNode(
            node_id=str(uuid.uuid4()),
            goal_id=goal.goal_id,
            agent_id=agent_ids[0 % len(agent_ids)] if agent_ids else "default",
            action=f"Coordinate: {goal.description}",
            metadata={"depth": 0, "is_coordinator": True, "total_stages": len(stages)},
            latency_estimate_ms=30.0,
            cost_estimate=0.02,
        )
        graph.add_node(coordinator)
        for i, stage in enumerate(stages):
            sub_coordinator = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=agent_ids[(i + 1) % len(agent_ids)] if agent_ids else "default",
                action=f"Sub-task: {stage.description}",
                depends_on=[coordinator.node_id],
                metadata={"depth": 1, "parent": coordinator.node_id, "sub_task_index": i},
                latency_estimate_ms=50.0 + (i * 25),
                cost_estimate=0.05,
            )
            graph.add_node(sub_coordinator)
            graph.add_edge(PlanEdge(source_id=coordinator.node_id, target_id=sub_coordinator.node_id))
            worker = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=agent_ids[(i + 2) % len(agent_ids)] if agent_ids else "default",
                action=f"Execute: {stage.description}",
                depends_on=[sub_coordinator.node_id],
                metadata={"depth": 2, "parent": sub_coordinator.node_id, "worker": True},
                latency_estimate_ms=100.0,
                cost_estimate=0.1,
            )
            graph.add_node(worker)
            graph.add_edge(PlanEdge(source_id=sub_coordinator.node_id, target_id=worker.node_id))
        return graph

    def _plan_reactive(self, goal: Goal, agent_ids: list[str]) -> PlanGraph:
        plan = Plan(plan_id=str(uuid.uuid4()), goal_id=goal.goal_id, strategy=PlanningStrategy.REACTIVE)
        graph = PlanGraph(plan)
        stages = self._build_multi_stage_goal(goal)
        monitor = PlanNode(
            node_id=str(uuid.uuid4()),
            goal_id=goal.goal_id,
            agent_id=agent_ids[0 % len(agent_ids)] if agent_ids else "default",
            action="Monitor execution and handle failures",
            metadata={"reactive": True, "is_monitor": True},
            latency_estimate_ms=20.0,
            cost_estimate=0.01,
        )
        graph.add_node(monitor)
        for i, stage in enumerate(stages):
            aid = agent_ids[(i + 1) % len(agent_ids)] if agent_ids else "default"
            fallback_aid = agent_ids[(i + 2) % len(agent_ids)] if agent_ids and len(agent_ids) > 2 else aid
            primary = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=aid,
                action=f"Primary: {stage.description}",
                metadata={"reactive": True, "fallback_agent": fallback_aid, "attempt": 1},
                latency_estimate_ms=100.0,
                cost_estimate=0.1,
                max_retries=2,
            )
            graph.add_node(primary)
            graph.add_edge(PlanEdge(source_id=monitor.node_id, target_id=primary.node_id))
            fallback = PlanNode(
                node_id=str(uuid.uuid4()),
                goal_id=stage.goal_id,
                agent_id=fallback_aid,
                action=f"Fallback: {stage.description}",
                depends_on=[primary.node_id],
                metadata={"reactive": True, "fallback": True, "attempt": 2},
                latency_estimate_ms=150.0,
                cost_estimate=0.15,
                max_retries=1,
            )
            graph.add_node(fallback)
            graph.add_edge(PlanEdge(source_id=primary.node_id, target_id=fallback.node_id, condition="on_failure"))
        return graph

    def _build_multi_stage_goal(self, goal: Goal) -> list[Goal]:
        if goal.sub_goals:
            stages: list[Goal] = []
            for sg in goal.sub_goals:
                stages.extend(self._build_multi_stage_goal(sg))
            return stages
        parts = goal.description.split(". ")
        if len(parts) >= 4:
            return [Goal(goal_id=str(uuid.uuid4()), description=p.strip()) for p in parts if p.strip()]
        return [goal]

    def _decompose_goal(self, goal: Goal) -> list[Goal]:
        if goal.sub_goals:
            result: list[Goal] = []
            for sg in goal.sub_goals:
                result.extend(self._decompose_goal(sg))
            return result
        return [goal]

    def decompose_goal(self, description: str, depth: int = 3) -> Goal:
        goal = Goal(goal_id=str(uuid.uuid4()), description=description)
        if depth <= 0:
            return goal
        sentences = [s.strip() for s in description.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        and_parts: list[str] = []
        for s in sentences:
            if " and " in s:
                and_parts.extend(p.strip() for p in s.split(" and ") if p.strip())
            else:
                and_parts.append(s)
        parts = and_parts if len(and_parts) >= 2 else self._DEFAULT_STAGES
        for part in parts[: depth * 2]:
            if depth > 1:
                sg = self.decompose_goal(part, depth - 1)
            else:
                sg = Goal(goal_id=str(uuid.uuid4()), description=part)
            goal.add_sub_goal(sg)
        return goal

    def replan(
        self,
        failed_plan: Plan,
        failed_node_id: str,
        agent_ids: list[str] | None = None,
    ) -> PlanGraph:
        logger.info("Replanning from failed node '%s' in plan '%s'", failed_node_id, failed_plan.plan_id)
        failed_node = failed_plan.nodes.get(failed_node_id)
        if failed_node is None:
            raise GoalDecompositionError(detail=f"Node '{failed_node_id}' not found in plan")
        goal = Goal(goal_id=failed_plan.goal_id, description=failed_node.action)
        strategy = failed_plan.strategy
        new_graph = self.plan(goal, strategy, agent_ids)
        completed_nodes = [n for n in failed_plan.nodes.values() if n.status == PlanNodeStatus.COMPLETED]
        for cn in completed_nodes:
            if cn.node_id != failed_node_id:
                new_graph.add_node(cn)
        return new_graph
