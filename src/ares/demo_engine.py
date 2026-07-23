from __future__ import annotations

import time
import uuid
from typing import Any

from ares.agents.builtin import (
    MemoryAgent,
    PlannerAgent,
    PredictAgent,
    ReflectionAgent,
)
from ares.agents.manager import AgentManager
from ares.agents.registry import AgentRegistry
from ares.agents.types import AgentPermissions, AgentStatus
from ares.demo_scenarios import DEMO_SCENARIOS
from ares.event_bus import EventBus
from ares.memory import MemoryManager
from ares.orchestration import OrchestrationEngine
from ares.orchestration.types import OrchestrationStrategyType, RunPolicies
from ares.planning import PlanningEngine, PlanningMetrics
from ares.tools.builtin import MemoryTool, PredictTool
from ares.tools.manager import ToolManager
from ares.tools.registry import ToolRegistry


class DemoEngine:
    def __init__(self) -> None:
        self._event_bus = EventBus()
        self._memory_manager = MemoryManager()
        self._tool_registry = ToolRegistry()
        self._tool_manager = ToolManager(
            registry=self._tool_registry,
            event_bus=self._event_bus,
        )
        self._agent_registry = AgentRegistry()
        self._agent_manager = AgentManager(registry=self._agent_registry)
        self._planning_metrics = PlanningMetrics()
        self._planning_engine = PlanningEngine(
            metrics=self._planning_metrics,
            event_bus=self._event_bus,
            memory_manager=self._memory_manager,
            agent_manager=self._agent_manager,
            tool_manager=self._tool_manager,
        )
        self._orchestration_engine = OrchestrationEngine(
            agent_manager=self._agent_manager,
            registry=self._agent_registry,
            event_bus=self._event_bus,
        )
        self._initialized = False
        self._demo_results: dict[str, Any] = {}

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def memory_manager(self) -> MemoryManager:
        return self._memory_manager

    @property
    def tool_manager(self) -> ToolManager:
        return self._tool_manager

    @property
    def agent_manager(self) -> AgentManager:
        return self._agent_manager

    @property
    def planning_engine(self) -> PlanningEngine:
        return self._planning_engine

    @property
    def orchestration_engine(self) -> OrchestrationEngine:
        return self._orchestration_engine

    @property
    def planning_metrics(self) -> PlanningMetrics:
        return self._planning_metrics

    @property
    def demo_results(self) -> dict[str, Any]:
        return dict(self._demo_results)

    def initialize(self) -> None:
        if self._initialized:
            return

        predict_tool = PredictTool()
        self._tool_registry.register(predict_tool)

        memory_tool = MemoryTool(manager=self._memory_manager)
        self._tool_registry.register(memory_tool)

        planner_agent = PlannerAgent(engine=self._planning_engine)
        self._agent_manager.register_existing_agent(
            planner_agent,
            permissions=AgentPermissions(agent_id="planner"),
        )

        predict_agent = PredictAgent()
        self._agent_manager.register_existing_agent(
            predict_agent,
            permissions=AgentPermissions(agent_id="predict"),
        )

        memory_agent = MemoryAgent(manager=self._memory_manager)
        self._agent_manager.register_existing_agent(
            memory_agent,
            permissions=AgentPermissions(agent_id="memory"),
        )

        reflection_agent = ReflectionAgent()
        self._agent_manager.register_existing_agent(
            reflection_agent,
            permissions=AgentPermissions(agent_id="reflection"),
        )

        self._agent_manager.set_event_bus(self._event_bus)
        self._tool_manager.set_event_bus(self._event_bus)

        self._initialized = True

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return DEMO_SCENARIOS.get(scenario_id)

    def list_scenarios(self) -> list[dict[str, str]]:
        return [
            {
                "id": sid,
                "name": s["name"],
                "description": s["description"],
            }
            for sid, s in DEMO_SCENARIOS.items()
        ]

    async def run_demo(
        self,
        scenario_id: str | None = None,
        question1: str = "",
        question2: str = "",
        goal: str = "",
        strategy: str = "LINEAR",
        agent_ids: list[str] | None = None,
        available_tools: list[str] | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        trace_id = str(uuid.uuid4())
        self._event_bus.clear()
        self._event_bus.emit(
            "demo",
            "demo_started",
            data={"trace_id": trace_id, "scenario_id": scenario_id or "custom"},
            trace_id=trace_id,
        )

        self.initialize()

        scenario = None
        if scenario_id:
            scenario = self.get_scenario(scenario_id)

        if scenario:
            q1 = question1 or scenario["question1"]
            q2 = question2 or scenario["question2"]
            g = goal or scenario["goal"]
            strat = scenario.get("strategy", strategy)
            agents = scenario.get("agent_ids", agent_ids or [])
            tools = scenario.get("available_tools", available_tools or [])
        else:
            q1 = question1
            q2 = question2
            g = goal or "Analyze semantic similarity between two questions"
            strat = strategy
            agents = agent_ids or ["planner", "predict", "memory", "reflection"]
            tools = available_tools or ["predict", "memory"]

        for aid in agents:
            try:
                agent_info = self._agent_registry.get_info(aid)
                if agent_info.status != AgentStatus.ACTIVE:
                    await self._agent_manager.activate_agent(aid)
            except Exception:
                pass

        self._event_bus.emit(
            "demo",
            "scenario_selected",
            data={"scenario_id": scenario_id or "custom", "question1": q1, "question2": q2},
            trace_id=trace_id,
        )

        overall_start = time.perf_counter()

        # ---- Phase 1: Planning ----
        planning_start = time.perf_counter()
        from ares.planning.types import PlanningStrategy

        self._event_bus.emit("demo", "planning_started", data={"goal": g}, trace_id=trace_id)

        goal_obj = self._planning_engine.create_goal(g, decompose=True)
        strategy_enum = getattr(PlanningStrategy, strat.upper(), PlanningStrategy.LINEAR)
        plan_graph = self._planning_engine.create_plan(
            goal_obj,
            strategy=strategy_enum,
            agent_ids=agents,
            available_tools=tools,
        )
        validation_errors = self._planning_engine.validate_plan(plan_graph, agents, tools)
        optimization_stats = self._planning_engine.optimize_plan(plan_graph)
        planning_time = (time.perf_counter() - planning_start) * 1000

        self._event_bus.emit(
            "demo",
            "planning_completed",
            data={
                "goal_id": goal_obj.goal_id,
                "plan_id": plan_graph.plan.plan_id,
                "node_count": len(plan_graph.plan.nodes),
                "validation_errors": validation_errors,
            },
            trace_id=trace_id,
        )

        # ---- Phase 2: Prediction ----
        prediction_start = time.perf_counter()
        self._event_bus.emit("demo", "prediction_started", data={"question1": q1, "question2": q2}, trace_id=trace_id)

        from ares._engine import ARES

        engine = ARES()
        if model_name:
            engine = engine.with_model(model_name)
        elif scenario and "model_name" in scenario:
            engine = engine.with_model(scenario["model_name"])
        prediction_result = engine.predict(q1, q2)
        prediction_time = (time.perf_counter() - prediction_start) * 1000

        self._event_bus.emit(
            "demo",
            "prediction_completed",
            data={
                "prediction": prediction_result.prediction,
                "confidence": prediction_result.confidence,
            },
            trace_id=trace_id,
        )

        # ---- Phase 3: Memory Storage ----
        memory_start = time.perf_counter()
        self._event_bus.emit("demo", "memory_write_started", trace_id=trace_id)

        mem_entry = self._memory_manager.store(
            key=f"prediction:{goal_obj.goal_id}",
            value={
                "question1": q1,
                "question2": q2,
                "prediction": prediction_result.prediction,
                "confidence": prediction_result.confidence,
                "model": prediction_result.model_name,
            },
            tags=["prediction", "demo"],
            agent_id="predict",
        )
        memory_write_time = (time.perf_counter() - memory_start) * 1000

        self._event_bus.emit(
            "demo",
            "memory_write_completed",
            data={
                "memory_id": mem_entry.memory_id,
                "key": mem_entry.key,
            },
            trace_id=trace_id,
        )

        # ---- Phase 4: Memory Read ----
        memory_read_start = time.perf_counter()
        self._event_bus.emit("demo", "memory_read_started", trace_id=trace_id)

        memory_entries = self._memory_manager.search("prediction:", limit=10)
        memory_read_time = (time.perf_counter() - memory_read_start) * 1000

        self._event_bus.emit(
            "demo",
            "memory_read_completed",
            data={
                "entry_count": len(memory_entries),
            },
            trace_id=trace_id,
        )

        # ---- Phase 5: Reflection ----
        reflection_start = time.perf_counter()
        self._event_bus.emit("demo", "reflection_started", trace_id=trace_id)

        reflection_result = {}
        try:
            from duplicate_question_app._reflection.reflection_engine import (
                ReflectionEngine,
            )

            ref_engine = ReflectionEngine()
            ref = ref_engine.reflect(
                prediction={
                    "predicted_label": prediction_result.predicted_label,
                    "prediction": prediction_result.prediction,
                    "confidence": prediction_result.confidence,
                    "prob_duplicate": prediction_result.prob_duplicate,
                    "prob_non_duplicate": prediction_result.prob_non_duplicate,
                }
            )
            trust_score = ref.trust_score
            if trust_score is not None and (trust_score > 1.0 or trust_score < 0.0):
                trust_score = max(0.0, min(1.0, trust_score))
            reflection_result = {
                "trust_score": trust_score,
                "trust_level": ref.trust_level.value if ref.trust_level else None,
                "risk_level": ref.risk_level.value if ref.risk_level else None,
                "human_review_required": ref.human_review_required,
                "recommendations": [r.value for r in ref.recommendations],
            }
        except Exception:
            reflection_result = {
                "trust_score": max(0.0, min(1.0, prediction_result.confidence)),
                "trust_level": "medium" if prediction_result.confidence > 0.5 else "low",
                "risk_level": "low" if prediction_result.confidence > 0.7 else "medium",
                "human_review_required": prediction_result.confidence < 0.6,
                "recommendations": [],
            }

        reflection_time = (time.perf_counter() - reflection_start) * 1000

        self._event_bus.emit("demo", "reflection_completed", data=reflection_result, trace_id=trace_id)

        # ---- Phase 6: Store Reflection in Memory ----
        reflection_mem = self._memory_manager.store(
            key=f"reflection:{goal_obj.goal_id}",
            value=reflection_result,
            tags=["reflection", "demo"],
            agent_id="reflection",
        )

        # ---- Phase 7: Execution via Orchestrator ----
        execution_start = time.perf_counter()
        self._event_bus.emit("demo", "execution_started", data={"agent_ids": agents}, trace_id=trace_id)

        orchestration_result = None
        if agents:
            try:
                orchestration_result = await self._orchestration_engine.run_agents(
                    agent_ids=agents,
                    input={
                        "question1": q1,
                        "question2": q2,
                        "goal_description": g,
                        "prediction": {
                            "predicted_label": prediction_result.predicted_label,
                            "prediction": prediction_result.prediction,
                            "confidence": prediction_result.confidence,
                            "prob_duplicate": prediction_result.prob_duplicate,
                            "prob_non_duplicate": prediction_result.prob_non_duplicate,
                        },
                        "result": {
                            "predicted_label": prediction_result.predicted_label,
                            "prediction": prediction_result.prediction,
                            "confidence": prediction_result.confidence,
                        },
                        "action": "full_cycle",
                        "strategy": strat,
                        "agent_ids": agents,
                        "available_tools": tools,
                    },
                    strategy=OrchestrationStrategyType.SEQUENTIAL,
                    policies=RunPolicies(
                        timeout_seconds=120.0,
                        max_retries=2,
                    ),
                )
            except Exception as e:
                self._event_bus.emit("demo", "execution_error", data={"error": str(e)}, trace_id=trace_id)

        execution_time = (time.perf_counter() - execution_start) * 1000

        total_time = (time.perf_counter() - overall_start) * 1000

        self._event_bus.emit(
            "demo",
            "demo_completed",
            data={
                "total_time_ms": total_time,
            },
            trace_id=trace_id,
        )

        result = {
            "trace_id": trace_id,
            "scenario_id": scenario_id or "custom",
            "goal": {
                "goal_id": goal_obj.goal_id,
                "description": goal_obj.description,
                "status": goal_obj.status.name,
                "sub_goals": [{"goal_id": sg.goal_id, "description": sg.description} for sg in goal_obj.sub_goals],
            },
            "plan": {
                "plan_id": plan_graph.plan.plan_id,
                "strategy": plan_graph.plan.strategy.name,
                "status": plan_graph.plan.status.name,
                "node_count": len(plan_graph.plan.nodes),
                "edge_count": len(plan_graph.plan.edges),
                "nodes": [
                    {
                        "node_id": n.node_id,
                        "agent_id": n.agent_id,
                        "action": n.action,
                        "status": n.status.name,
                        "depends_on": list(n.depends_on),
                    }
                    for n in plan_graph.plan.nodes.values()
                ],
                "edges": [{"source_id": e.source_id, "target_id": e.target_id} for e in plan_graph.plan.edges],
                "execution_order": plan_graph.get_execution_order(),
                "complexity": plan_graph.get_complexity(),
            },
            "validation_errors": validation_errors,
            "optimization_stats": optimization_stats,
            "prediction": {
                "question1": q1,
                "question2": q2,
                "predicted_label": prediction_result.predicted_label,
                "prediction": prediction_result.prediction,
                "confidence": prediction_result.confidence,
                "prob_duplicate": prediction_result.prob_duplicate,
                "prob_non_duplicate": prediction_result.prob_non_duplicate,
                "model_name": prediction_result.model_name,
                "latency_ms": prediction_result.latency_ms,
                "trust_score": max(
                    0.0, min(1.0, prediction_result.trust_score if prediction_result.trust_score is not None else 0.0)
                ),
            },
            "reflection": reflection_result,
            "memory": {
                "stored": {
                    "memory_id": mem_entry.memory_id,
                    "key": mem_entry.key,
                },
                "reflection_memory_id": reflection_mem.memory_id,
                "retrieved_count": len(memory_entries),
                "retrieved_entries": [
                    {
                        "memory_id": e.memory_id,
                        "key": e.key,
                        "value": e.value,
                        "tier": e.tier.name,
                        "score": e.score,
                    }
                    for e in memory_entries
                ],
            },
            "orchestration": {
                "status": orchestration_result.status.name if orchestration_result else "skipped",
                "agent_results": [
                    {
                        "agent_id": r.agent_id,
                        "status": r.status.name,
                        "processing_time_ms": r.processing_time_ms,
                    }
                    for r in (orchestration_result.agent_results if orchestration_result else [])
                ],
            }
            if orchestration_result
            else {"status": "skipped"},
            "execution_tree": plan_graph.get_execution_order(),
            "timeline": {
                "planning_time_ms": planning_time,
                "prediction_time_ms": prediction_time,
                "memory_write_time_ms": memory_write_time,
                "memory_read_time_ms": memory_read_time,
                "reflection_time_ms": reflection_time,
                "execution_time_ms": execution_time,
                "total_time_ms": total_time,
            },
            "events": [
                {
                    "event_id": e.event_id,
                    "source": e.source,
                    "event_type": e.event_type,
                    "data": e.data,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self._event_bus.get_events(limit=50)
            ],
            "metrics": self._planning_metrics.summary(),
            "final_response": (
                f"Prediction: {prediction_result.prediction} "
                f"(confidence: {prediction_result.confidence:.2%}, "
                f"model: {prediction_result.model_name})"
            ),
        }

        self._demo_results[trace_id] = result
        return result

    def get_demo_result(self, trace_id: str) -> dict[str, Any] | None:
        return self._demo_results.get(trace_id)  # type: ignore[no-any-return]

    def list_demo_results(self) -> list[dict[str, Any]]:
        return [
            {
                "trace_id": tid,
                "scenario_id": r.get("scenario_id"),
                "prediction": r.get("prediction", {}).get("prediction"),
                "confidence": r.get("prediction", {}).get("confidence"),
                "total_time_ms": r.get("timeline", {}).get("total_time_ms"),
                "plan_status": r.get("plan", {}).get("status"),
            }
            for tid, r in self._demo_results.items()
        ]

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": tid,
                "name": self._tool_registry.get(tid).metadata.name,
                "status": self._tool_registry.get_status(tid).name,
            }
            for tid in self._tool_registry.list_all()
        ]

    def get_agents(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": info.metadata.agent_id,
                "name": info.metadata.name,
                "status": info.status.name,
                "invocations": info.total_invocations,
            }
            for info in self._agent_registry.list_by_status()
        ]

    def get_memory(self) -> dict[str, Any]:
        stats = self._memory_manager.get_stats()
        entries = self._memory_manager.search("", limit=50)
        return {
            "stats": {
                "total_entries": stats.total_entries,
                "entries_by_tier": stats.entries_by_tier,
                "entries_by_domain": stats.entries_by_domain,
            },
            "entries": [
                {
                    "memory_id": e.memory_id,
                    "key": e.key,
                    "value": e.value if isinstance(e.value, (str, int, float, bool, type(None))) else str(e.value),
                    "tier": e.tier.name,
                    "domain": e.domain.name,
                    "score": e.score,
                    "tags": e.tags,
                }
                for e in entries
            ],
        }

    def get_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "source": e.source,
                "event_type": e.event_type,
                "data": e.data,
                "severity": e.severity.name,
                "timestamp": e.timestamp.isoformat(),
                "trace_id": e.trace_id,
            }
            for e in self._event_bus.get_events(limit=limit)
        ]

    def get_metrics(self) -> dict[str, Any]:
        return self._planning_metrics.summary()  # type: ignore[no-any-return]
