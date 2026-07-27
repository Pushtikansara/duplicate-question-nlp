from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ares.planning.context import PlanningContext
from ares.planning.events import PlanningEvent, PlanningEventType
from ares.planning.executor import PlanExecutor
from ares.planning.graph import PlanGraph
from ares.planning.metrics import PlanningMetrics
from ares.planning.optimizer import PlanOptimizer
from ares.planning.planner import Planner
from ares.planning.types import Goal, GoalStatus, Plan, PlanningStrategy, PlanResult, PlanStatus
from ares.planning.validator import PlanValidator

logger = logging.getLogger(__name__)


class PlanningEngine:
    def __init__(
        self,
        planner: Planner | None = None,
        validator: PlanValidator | None = None,
        optimizer: PlanOptimizer | None = None,
        executor: PlanExecutor | None = None,
        metrics: PlanningMetrics | None = None,
        event_bus: Any = None,
        memory_manager: Any = None,
        agent_manager: Any = None,
        tool_manager: Any = None,
        orchestrator: Any = None,
    ) -> None:
        self._planner = planner or Planner()
        self._validator = validator or PlanValidator()
        self._optimizer = optimizer or PlanOptimizer()
        self._executor = executor or PlanExecutor(
            orchestrator=orchestrator,
            agent_manager=agent_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager,
            event_bus=event_bus,
            metrics=metrics,
        )
        self._metrics = metrics or PlanningMetrics()
        self._event_bus = event_bus
        self._memory_manager = memory_manager
        self._agent_manager = agent_manager
        self._tool_manager = tool_manager
        self._orchestrator = orchestrator
        self._plans: dict[str, Plan] = {}
        self._goals: dict[str, Goal] = {}
        self._contexts: dict[str, PlanningContext] = {}

    @property
    def planner(self) -> Planner:
        return self._planner

    @property
    def validator(self) -> PlanValidator:
        return self._validator

    @property
    def optimizer(self) -> PlanOptimizer:
        return self._optimizer

    @property
    def executor(self) -> PlanExecutor:
        return self._executor

    @property
    def metrics(self) -> PlanningMetrics:
        return self._metrics

    def create_goal(
        self,
        description: str,
        decompose: bool = True,
        depth: int = 3,
    ) -> Goal:
        goal = (
            self._planner.decompose_goal(description, depth=depth)
            if decompose
            else Goal(
                goal_id=str(uuid.uuid4()),
                description=description,
            )
        )
        goal.status = GoalStatus.PENDING
        self._goals[goal.goal_id] = goal
        self._emit_event(PlanningEventType.GOAL_CREATED, goal_id=goal.goal_id)
        return goal

    def create_plan(
        self,
        goal: Goal,
        strategy: PlanningStrategy = PlanningStrategy.LINEAR,
        agent_ids: list[str] | None = None,
        available_tools: list[str] | None = None,
        context: PlanningContext | None = None,
    ) -> PlanGraph:
        start = time.perf_counter()

        goal.status = GoalStatus.PLANNING
        graph = self._planner.plan(goal, strategy, agent_ids, available_tools)
        graph.plan.status = PlanStatus.DRAFT

        self._plans[graph.plan.plan_id] = graph.plan
        if context:
            self._contexts[graph.plan.plan_id] = context

        elapsed = (time.perf_counter() - start) * 1000
        self._metrics.record_planning_latency(elapsed)
        self._metrics.record_plan_created(len(graph.plan.nodes), len(graph.plan.edges))

        self._emit_event(PlanningEventType.PLAN_CREATED, graph.plan.plan_id, goal.goal_id)

        if self._memory_manager is not None:
            from contextlib import suppress

            with suppress(Exception):
                self._memory_manager.store(
                    key=f"plan:{graph.plan.plan_id}",
                    value={
                        "goal_id": goal.goal_id,
                        "strategy": strategy.name,
                        "node_count": len(graph.plan.nodes),
                        "description": goal.description,
                    },
                    tags=["planning"],
                )

        return graph

    def validate_plan(
        self,
        graph: PlanGraph,
        available_agents: list[str] | None = None,
        available_tools: list[str] | None = None,
    ) -> list[str]:
        errors = self._validator.validate(graph, available_agents, available_tools)
        if not errors:
            graph.plan.status = PlanStatus.VALIDATED
        self._emit_event(PlanningEventType.PLAN_VALIDATED, graph.plan.plan_id, graph.plan.goal_id)
        return errors

    def optimize_plan(
        self,
        graph: PlanGraph,
        optimize_latency: bool = True,
        optimize_parallelism: bool = True,
        optimize_cost: bool = False,
        optimize_retries: bool = False,
    ) -> dict[str, Any]:
        stats = self._optimizer.optimize(graph, optimize_latency, optimize_parallelism, optimize_cost, optimize_retries)
        graph.plan.status = PlanStatus.OPTIMIZED
        self._metrics.record_optimization_gain(
            stats["before"]["total_latency_estimate_ms"],
            stats["after"]["total_latency_estimate_ms"],
        )
        self._emit_event(PlanningEventType.PLAN_OPTIMIZED, graph.plan.plan_id, graph.plan.goal_id)
        return stats

    async def execute_plan(
        self,
        graph: PlanGraph,
        context: dict[str, Any] | None = None,
    ) -> PlanResult:
        goal = self._goals.get(graph.plan.goal_id)
        if goal:
            goal.status = GoalStatus.EXECUTING
        result = await self._executor.execute(graph, context)
        if goal:
            goal.status = GoalStatus.COMPLETED if result.status == PlanStatus.COMPLETED else GoalStatus.FAILED

        if self._memory_manager is not None:
            from contextlib import suppress

            with suppress(Exception):
                self._memory_manager.store(
                    key=f"plan-result:{result.plan_id}",
                    value={
                        "status": result.status.name,
                        "total_latency_ms": result.total_latency_ms,
                        "total_cost": result.total_cost,
                        "node_count": len(result.node_results),
                    },
                    tags=["planning", "result"],
                )

        return result

    async def full_cycle(
        self,
        goal_description: str,
        strategy: PlanningStrategy = PlanningStrategy.LINEAR,
        agent_ids: list[str] | None = None,
        available_tools: list[str] | None = None,
        decompose: bool = True,
        validate: bool = True,
        optimize: bool = True,
        execute: bool = True,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        goal = self.create_goal(goal_description, decompose=decompose)
        graph = self.create_plan(goal, strategy, agent_ids, available_tools)

        plan_result = None
        validation_errors = []
        optimization_stats = {}

        if validate:
            validation_errors = self.validate_plan(graph, agent_ids, available_tools)

        if optimize and not validation_errors:
            optimization_stats = self.optimize_plan(graph)

        if execute and not validation_errors:
            plan_result = await self.execute_plan(graph)

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "goal": goal,
            "plan_graph": graph,
            "plan_result": plan_result,
            "validation_errors": validation_errors,
            "optimization_stats": optimization_stats,
            "total_time_ms": elapsed,
        }

    def cancel_plan(self, plan_id: str) -> None:
        self._executor.cancel(plan_id)
        plan = self._plans.get(plan_id)
        if plan:
            plan.status = PlanStatus.CANCELLED
        self._emit_event(PlanningEventType.PLAN_CANCELLED, plan_id)

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def get_goal(self, goal_id: str) -> Goal | None:
        return self._goals.get(goal_id)

    def get_context(self, plan_id: str) -> PlanningContext | None:
        return self._contexts.get(plan_id)

    def get_all_plans(self) -> list[Plan]:
        return list(self._plans.values())

    def get_all_goals(self) -> list[Goal]:
        return list(self._goals.values())

    def _emit_event(
        self,
        event_type: PlanningEventType,
        plan_id: str = "",
        goal_id: str = "",
        error: str | None = None,
    ) -> None:
        if self._event_bus is None:
            return
        try:
            event = PlanningEvent(
                event_type=event_type,
                plan_id=plan_id,
                goal_id=goal_id,
                error=error,
            )
            self._event_bus.publish(event)
        except Exception as exc:
            logger.warning("Failed to publish error event for goal '%s': %s", goal_id, exc)
