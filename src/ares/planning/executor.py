from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from ares.planning.events import PlanningEvent, PlanningEventType
from ares.planning.graph import PlanGraph
from ares.planning.metrics import PlanningMetrics
from ares.planning.types import Plan, PlanNode, PlanNodeStatus, PlanResult, PlanStatus

logger = logging.getLogger(__name__)


class PlanExecutor:
    def __init__(
        self,
        orchestrator: Any = None,
        agent_manager: Any = None,
        tool_manager: Any = None,
        memory_manager: Any = None,
        event_bus: Any = None,
        metrics: PlanningMetrics | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._agent_manager = agent_manager
        self._tool_manager = tool_manager
        self._memory_manager = memory_manager
        self._event_bus = event_bus
        self._metrics = metrics or PlanningMetrics()
        self._cancelled: set[str] = set()

    @property
    def metrics(self) -> PlanningMetrics:
        return self._metrics

    async def execute(
        self,
        graph: PlanGraph,
        context: dict[str, Any] | None = None,
    ) -> PlanResult:
        plan = graph.plan
        plan.status = PlanStatus.RUNNING
        start_time = time.time()
        timeline: list[dict[str, Any]] = []
        node_results: dict[str, PlanNode] = {}

        self._emit_event(PlanningEventType.PLAN_STARTED, plan)

        try:
            execution_order = graph.get_execution_order()
            for _level_idx, level in enumerate(execution_order):
                if plan.plan_id in self._cancelled:
                    plan.status = PlanStatus.CANCELLED
                    self._emit_event(PlanningEventType.PLAN_CANCELLED, plan)
                    break

                tasks = []
                for node_id in level:
                    if node_id not in plan.nodes:
                        continue
                    node = plan.nodes[node_id]
                    if node.status == PlanNodeStatus.COMPLETED:
                        continue
                    tasks.append(self._execute_node(node, plan, context or {}))

                if tasks:
                    if any(plan.nodes[nid].metadata.get("parallel", False) for nid in level if nid in plan.nodes):
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, Exception):
                                logger.error("Parallel node execution failed: %s", result)
                    else:
                        for task in tasks:
                            result = await task
                            if isinstance(result, Exception):
                                logger.error("Sequential node execution failed: %s", result)

                for node_id in level:
                    if node_id in plan.nodes:
                        node = plan.nodes[node_id]
                        node_results[node_id] = node
                        timeline.append(
                            {
                                "node_id": node_id,
                                "agent_id": node.agent_id,
                                "action": node.action,
                                "status": node.status.name,
                                "latency_ms": (time.time() - start_time) * 1000,
                            }
                        )

            if plan.status != PlanStatus.CANCELLED:
                all_completed = all(
                    n.status == PlanNodeStatus.COMPLETED or n.status == PlanNodeStatus.SKIPPED
                    for n in plan.nodes.values()
                )
                if all_completed:
                    plan.status = PlanStatus.COMPLETED
                else:
                    plan.status = PlanStatus.PARTIAL

        except Exception as e:
            plan.status = PlanStatus.FAILED
            self._metrics.record_failure()
            self._emit_event(PlanningEventType.PLAN_FAILED, plan, error=str(e))
            logger.error("Plan execution failed: %s", e)

        plan.completed_at = datetime.now(timezone.utc)
        total_latency = (time.time() - start_time) * 1000
        total_cost = sum(n.cost_estimate for n in plan.nodes.values())

        self._metrics.record_execution_latency(total_latency)
        if plan.status == PlanStatus.COMPLETED:
            self._metrics.record_plan_completed()
        self._emit_event(
            PlanningEventType.PLAN_COMPLETED if plan.status == PlanStatus.COMPLETED else PlanningEventType.PLAN_FAILED,
            plan,
        )

        return PlanResult(
            plan_id=plan.plan_id,
            goal_id=plan.goal_id,
            status=plan.status,
            node_results=node_results,
            total_latency_ms=total_latency,
            total_cost=total_cost,
            execution_timeline=timeline,
            optimization_summary=plan.optimization_stats,
        )

    async def _execute_node(
        self,
        node: PlanNode,
        plan: Plan,
        context: dict[str, Any],
    ) -> None:
        node.status = PlanNodeStatus.RUNNING
        self._emit_event(PlanningEventType.PLAN_NODE_STARTED, plan, node_id=node.node_id)

        try:
            if self._orchestrator is not None:
                result = await self._orchestrator.run_single(
                    agent_id=node.agent_id,
                    input={
                        "action": node.action,
                        "goal_id": node.goal_id,
                        "node_id": node.node_id,
                        "context": context,
                        **node.input,
                    },
                )
                node.output = result
                node.status = PlanNodeStatus.COMPLETED
            elif self._agent_manager is not None:
                agent = self._agent_manager.registry.get(node.agent_id)
                if agent is None:
                    raise ValueError(f"Agent '{node.agent_id}' not found")
                output = await agent.execute(node.action, context=context)
                node.output = output
                node.status = PlanNodeStatus.COMPLETED
            else:
                node.status = PlanNodeStatus.COMPLETED
                node.output = {"executed": node.action}

            node.completed_at = datetime.now(timezone.utc)

            if self._memory_manager is not None and node.status == PlanNodeStatus.COMPLETED:
                from contextlib import suppress

                with suppress(Exception):
                    self._memory_manager.store(
                        key=f"plan:{plan.plan_id}:node:{node.node_id}",
                        value={
                            "action": node.action,
                            "agent_id": node.agent_id,
                            "status": node.status.name,
                            "output": str(node.output),
                        },
                        tags=["planning", "execution"],
                    )

            self._emit_event(PlanningEventType.PLAN_NODE_COMPLETED, plan, node_id=node.node_id)

        except Exception as e:
            node.error = str(e)
            node.retry_count += 1
            self._metrics.record_retry()

            if node.retry_count < node.max_retries:
                node.status = PlanNodeStatus.PENDING
                self._emit_event(PlanningEventType.PLAN_NODE_RETRYING, plan, node_id=node.node_id, error=str(e))
                await self._execute_node(node, plan, context)
            else:
                node.status = PlanNodeStatus.FAILED
                self._emit_event(PlanningEventType.PLAN_NODE_FAILED, plan, node_id=node.node_id, error=str(e))

    def cancel(self, plan_id: str) -> None:
        self._cancelled.add(plan_id)
        logger.info("Cancellation requested for plan '%s'", plan_id)

    async def execute_partial(
        self,
        graph: PlanGraph,
        from_node_id: str,
        context: dict[str, Any] | None = None,
    ) -> PlanResult:
        plan = graph.plan
        plan.status = PlanStatus.RUNNING
        found = False
        for node in plan.nodes.values():
            if node.node_id == from_node_id:
                node.status = PlanNodeStatus.PENDING
                found = True
            elif not found:
                node.status = PlanNodeStatus.SKIPPED
        if not found:
            raise ValueError(f"Node '{from_node_id}' not found in plan")
        return await self.execute(graph, context)

    async def resume(
        self,
        graph: PlanGraph,
        context: dict[str, Any] | None = None,
    ) -> PlanResult:
        plan = graph.plan
        for node in plan.nodes.values():
            if node.status == PlanNodeStatus.RUNNING:
                node.status = PlanNodeStatus.PENDING
        plan.status = PlanStatus.RUNNING
        self._emit_event(PlanningEventType.PLAN_RESUMED, plan)
        return await self.execute(graph, context)

    def _emit_event(
        self,
        event_type: PlanningEventType,
        plan: Plan,
        node_id: str = "",
        error: str | None = None,
    ) -> None:
        if self._event_bus is None:
            return
        try:
            event = PlanningEvent(
                event_type=event_type,
                plan_id=plan.plan_id,
                goal_id=plan.goal_id,
                node_id=node_id,
                error=error,
            )
            self._event_bus.publish(event)
        except Exception as exc:
            logger.warning("Failed to publish error event for node '%s': %s", node_id, exc)
