from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ares.api.dependencies import get_request_id

if TYPE_CHECKING:
    from ares.demo_engine import DemoEngine

logger = logging.getLogger(__name__)
router = APIRouter()

_DEMO_ENGINE: DemoEngine | None = None


def _get_engine() -> DemoEngine:
    global _DEMO_ENGINE
    if _DEMO_ENGINE is None:
        from ares.demo_engine import DemoEngine

        _DEMO_ENGINE = DemoEngine()
        _DEMO_ENGINE.initialize()
    return _DEMO_ENGINE


class ChatRequest(BaseModel):
    question1: str = Field(..., min_length=1, max_length=1000)
    question2: str = Field(..., min_length=1, max_length=1000)
    scenario_id: str | None = None
    goal: str = ""
    strategy: str = "LINEAR"
    agent_ids: list[str] | None = None
    available_tools: list[str] | None = None
    model_name: str | None = None


class PlanRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=1000)
    strategy: str = "LINEAR"
    agent_ids: list[str] | None = None
    available_tools: list[str] | None = None


class PlanResponse(BaseModel):
    plan_id: str = ""
    goal_id: str = ""
    strategy: str = ""
    node_count: int = 0
    edge_count: int = 0
    validation_errors: list[str] = Field(default_factory=list)
    execution_order: list[list[str]] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/ares/chat")
async def ares_chat(
    req: ChatRequest,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    engine = _get_engine()
    try:
        result = await engine.run_demo(
            scenario_id=req.scenario_id,
            question1=req.question1,
            question2=req.question2,
            goal=req.goal,
            strategy=req.strategy,
            agent_ids=req.agent_ids,
            available_tools=req.available_tools,
            model_name=req.model_name,
        )
        result["request_id"] = request_id
        return result
    except Exception as e:
        logger.exception("ARES chat failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ares/plan")
async def ares_plan(
    req: PlanRequest,
    request_id: str = Depends(get_request_id),
) -> PlanResponse:
    engine = _get_engine()
    try:
        from ares.planning.types import PlanningStrategy

        goal_obj = engine.planning_engine.create_goal(req.goal, decompose=True)
        strategy_enum = getattr(PlanningStrategy, req.strategy.upper(), PlanningStrategy.LINEAR)
        plan_graph = engine.planning_engine.create_plan(
            goal_obj,
            strategy=strategy_enum,
            agent_ids=req.agent_ids,
            available_tools=req.available_tools,
        )
        validation_errors = engine.planning_engine.validate_plan(
            plan_graph,
            req.agent_ids,
            req.available_tools,
        )
        return PlanResponse(
            plan_id=plan_graph.plan.plan_id,
            goal_id=goal_obj.goal_id,
            strategy=plan_graph.plan.strategy.name,
            node_count=len(plan_graph.plan.nodes),
            edge_count=len(plan_graph.plan.edges),
            validation_errors=validation_errors,
            execution_order=plan_graph.get_execution_order(),
            nodes=[
                {
                    "node_id": n.node_id,
                    "agent_id": n.agent_id,
                    "action": n.action,
                    "status": n.status.name,
                    "depends_on": list(n.depends_on),
                }
                for n in plan_graph.plan.nodes.values()
            ],
            edges=[{"source_id": e.source_id, "target_id": e.target_id} for e in plan_graph.plan.edges],
        )
    except Exception as e:
        logger.exception("ARES plan failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ares/plans/{plan_id}")
async def get_plan(
    plan_id: str,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    engine = _get_engine()
    plan = engine.planning_engine.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found")
    return {
        "plan_id": plan.plan_id,
        "goal_id": plan.goal_id,
        "status": plan.status.name,
        "strategy": plan.strategy.name,
        "node_count": len(plan.nodes),
        "edge_count": len(plan.edges),
        "nodes": [
            {
                "node_id": n.node_id,
                "agent_id": n.agent_id,
                "action": n.action,
                "status": n.status.name,
                "depends_on": list(n.depends_on),
            }
            for n in plan.nodes.values()
        ],
        "edges": [{"source_id": e.source_id, "target_id": e.target_id} for e in plan.edges],
        "created_at": plan.created_at.isoformat(),
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
    }


@router.get("/ares/memory")
async def get_memory(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    engine = _get_engine()
    return engine.get_memory()


@router.get("/ares/tools")
async def get_tools(
    request_id: str = Depends(get_request_id),
) -> list[dict[str, Any]]:
    engine = _get_engine()
    return engine.get_tools()


@router.get("/ares/agents")
async def get_agents(
    request_id: str = Depends(get_request_id),
) -> list[dict[str, Any]]:
    engine = _get_engine()
    return engine.get_agents()


@router.get("/ares/events")
async def get_events(
    limit: int = Query(default=100, ge=1, le=1000),
    request_id: str = Depends(get_request_id),
) -> list[dict[str, Any]]:
    engine = _get_engine()
    return engine.get_events(limit=limit)


@router.get("/ares/metrics")
async def get_metrics(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    engine = _get_engine()
    return engine.get_metrics()


@router.get("/ares/health")
async def ares_health(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    engine = _get_engine()
    try:
        agent_count = len(engine.get_agents())
        tool_count = len(engine.get_tools())
        memory_stats = engine.get_memory().get("stats", {})
        return {
            "status": "healthy",
            "agents": agent_count,
            "tools": tool_count,
            "memory_entries": memory_stats.get("total_entries", 0),
            "events": len(engine.get_events(limit=1)),
            "initialized": engine._initialized,
            "request_id": request_id,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "request_id": request_id,
        }


@router.get("/ares/scenarios")
async def list_scenarios(
    request_id: str = Depends(get_request_id),
) -> list[dict[str, str]]:
    engine = _get_engine()
    return engine.list_scenarios()
