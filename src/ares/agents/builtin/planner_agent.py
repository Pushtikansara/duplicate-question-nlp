from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)
from ares.planning import (
    PlanningEngine,
    PlanningMetrics,
    PlanningStrategy,
)

logger = logging.getLogger(__name__)


class PlannerAgent(Agent):
    metadata = AgentMetadata(
        agent_id="planner",
        name="Planning Agent",
        version="1.0",
        description="Generates, validates, optimizes, and executes plans using the PlanningEngine",
        capabilities=frozenset({AgentCapability.PLANNING}),
        timeout_seconds=120.0,
        max_retries=2,
    )

    def __init__(self, engine: PlanningEngine | None = None) -> None:
        super().__init__()
        self._engine = engine or PlanningEngine(metrics=PlanningMetrics())
        self._last_plan_result: dict[str, Any] = {}

    @property
    def engine(self) -> PlanningEngine:
        return self._engine

    @property
    def last_plan_result(self) -> dict[str, Any]:
        return self._last_plan_result

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        action = input.get("action", "plan")
        goal_description = input.get("goal_description", input.get("context", {}).get("goal", ""))

        try:
            if action == "plan" or action == "full_cycle":
                strategy_name = input.get("strategy", "LINEAR")
                strategy = getattr(PlanningStrategy, strategy_name.upper(), PlanningStrategy.LINEAR)
                agent_ids = input.get("agent_ids", [])
                available_tools = input.get("available_tools", [])

                result = await self._engine.full_cycle(
                    goal_description=goal_description,
                    strategy=strategy,
                    agent_ids=agent_ids,
                    available_tools=available_tools,
                    decompose=input.get("decompose", True),
                    validate=input.get("validate", True),
                    optimize=input.get("optimize", True),
                    execute=input.get("execute", True),
                )
                self._last_plan_result = {
                    "goal": {
                        "goal_id": result["goal"].goal_id,
                        "description": result["goal"].description,
                        "status": result["goal"].status.name,
                        "sub_goals": [
                            {"goal_id": sg.goal_id, "description": sg.description} for sg in result["goal"].sub_goals
                        ],
                    },
                    "plan_graph": result["plan_graph"].to_dict() if result["plan_graph"] else None,
                    "plan_result": {
                        "status": result["plan_result"].status.name if result["plan_result"] else None,
                        "total_latency_ms": result["plan_result"].total_latency_ms if result["plan_result"] else 0,
                        "total_cost": result["plan_result"].total_cost if result["plan_result"] else 0,
                        "execution_timeline": result["plan_result"].execution_timeline if result["plan_result"] else [],
                    }
                    if result["plan_result"]
                    else None,
                    "validation_errors": result["validation_errors"],
                    "optimization_stats": result["optimization_stats"],
                    "total_time_ms": result["total_time_ms"],
                }

                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result=self._last_plan_result,
                    processing_time_ms=elapsed,
                )

            elif action == "create_goal":
                goal = self._engine.create_goal(
                    goal_description,
                    decompose=input.get("decompose", True),
                    depth=input.get("depth", 3),
                )
                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={
                        "goal_id": goal.goal_id,
                        "description": goal.description,
                        "status": goal.status.name,
                        "sub_goals": [{"goal_id": sg.goal_id, "description": sg.description} for sg in goal.sub_goals],
                    },
                    processing_time_ms=elapsed,
                )

            elif action == "get_plans":
                plans = self._engine.get_all_plans()
                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={
                        "plans": [
                            {
                                "plan_id": p.plan_id,
                                "goal_id": p.goal_id,
                                "status": p.status.name,
                                "strategy": p.strategy.name,
                                "node_count": len(p.nodes),
                                "edge_count": len(p.edges),
                            }
                            for p in plans
                        ],
                        "count": len(plans),
                    },
                    processing_time_ms=elapsed,
                )

            else:
                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={"message": f"Unknown action: {action}"},
                    processing_time_ms=elapsed,
                )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception("PlannerAgent failed")
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error=str(e),
                processing_time_ms=elapsed,
            )
