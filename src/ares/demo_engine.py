from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ares._config import get_config
from ares._engine import ARES
from ares.agents.builtin import MemoryAgent, PlannerAgent, PredictAgent, ReflectionAgent
from ares.agents.decision_agent import DecisionAgent
from ares.agents.manager import AgentManager
from ares.agents.registry import AgentRegistry
from ares.agents.types import AgentPermissions, AgentStatus
from ares.confidence import (
    compute_final_confidence,
    compute_risk_level,
    compute_trust_level,
    compute_trust_score,
    generate_explanation,
)
from ares.demo_scenarios import DEMO_SCENARIOS
from ares.event_bus import EventBus
from ares.memory import MemoryManager
from ares.orchestration import OrchestrationEngine
from ares.orchestration.types import OrchestrationStrategyType, RunPolicies
from ares.planning import PlanningEngine, PlanningMetrics
from ares.semantic_validator import validate_semantic
from ares.tools.builtin import MemoryTool, PredictTool
from ares.tools.manager import ToolManager
from ares.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class DemoEngine:
    def __init__(self) -> None:
        self._event_bus = EventBus()
        self._memory_manager = MemoryManager()
        self._tool_registry = ToolRegistry()
        self._tool_manager = ToolManager(registry=self._tool_registry, event_bus=self._event_bus)
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
    def planning_engine(self) -> PlanningEngine:
        return self._planning_engine

    def initialize(self) -> None:
        if self._initialized:
            return

        predict_tool = PredictTool()
        self._tool_registry.register(predict_tool)
        memory_tool = MemoryTool(manager=self._memory_manager)
        self._tool_registry.register(memory_tool)

        planner_agent = PlannerAgent(engine=self._planning_engine)
        self._agent_manager.register_existing_agent(planner_agent, permissions=AgentPermissions(agent_id="planner"))

        predict_agent = PredictAgent()
        self._agent_manager.register_existing_agent(predict_agent, permissions=AgentPermissions(agent_id="predict"))

        memory_agent = MemoryAgent(manager=self._memory_manager)
        self._agent_manager.register_existing_agent(memory_agent, permissions=AgentPermissions(agent_id="memory"))

        reflection_agent = ReflectionAgent()
        self._agent_manager.register_existing_agent(
            reflection_agent, permissions=AgentPermissions(agent_id="reflection")
        )

        decision_agent = DecisionAgent()
        self._agent_manager.register_existing_agent(decision_agent, permissions=AgentPermissions(agent_id="decision"))

        self._agent_manager.set_event_bus(self._event_bus)
        self._tool_manager.set_event_bus(self._event_bus)
        self._initialized = True

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return DEMO_SCENARIOS.get(scenario_id)

    def list_scenarios(self) -> list[dict[str, str]]:
        return [{"id": sid, "name": s["name"], "description": s["description"]} for sid, s in DEMO_SCENARIOS.items()]

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
            agents = scenario.get("agent_ids", agent_ids or [])
            tools = scenario.get("available_tools", available_tools or [])
        else:
            cfg = (get_config("inference") or {}).get("demo", {})
            q1 = question1
            q2 = question2
            g = goal or cfg.get("default_goal", "Analyze semantic similarity between two questions")
            agents = agent_ids or cfg.get("default_agents", ["planner", "predict", "memory", "reflection"])
            tools = available_tools or cfg.get("default_tools", ["predict", "memory"])

        for aid in agents:
            try:
                agent_info = self._agent_registry.get_info(aid)
                if agent_info.status != AgentStatus.ACTIVE:
                    await self._agent_manager.activate_agent(aid)
            except Exception as exc:
                logger.warning("Failed to activate agent '%s': %s", aid, exc)

        self._event_bus.emit(
            "demo",
            "scenario_selected",
            data={"scenario_id": scenario_id or "custom", "question1": q1, "question2": q2},
            trace_id=trace_id,
        )

        overall_start = time.perf_counter()

        # Phase 1: Planning
        planning_start = time.perf_counter()
        from ares.orchestration.strategy import resolve_planning_strategy

        self._event_bus.emit("demo", "planning_started", data={"goal": g}, trace_id=trace_id)
        goal_obj = self._planning_engine.create_goal(g, decompose=True)
        strategy_enum = resolve_planning_strategy(name=strategy)
        plan_graph = self._planning_engine.create_plan(
            goal_obj, strategy=strategy_enum, agent_ids=agents, available_tools=tools
        )
        validation_errors = self._planning_engine.validate_plan(plan_graph, agents, tools)
        optimization_stats = self._planning_engine.optimize_plan(plan_graph)
        planning_time = (time.perf_counter() - planning_start) * 1000

        # Phase 2: Prediction + Semantic Validation + Reflection
        prediction_start = time.perf_counter()
        self._event_bus.emit("demo", "prediction_started", data={"question1": q1, "question2": q2}, trace_id=trace_id)

        resolved_model = model_name or (scenario.get("model_name") if scenario else None) or ""
        mode = scenario.get("mode", "selected") if scenario else "selected"

        engine = ARES().with_reflection(False)
        if resolved_model:
            engine = engine.with_model(resolved_model)
        if mode == "fusion":
            engine = engine.with_fusion_mode("fusion")

        prediction_result = engine.predict(q1, q2)
        prediction_time = (time.perf_counter() - prediction_start) * 1000

        # Semantic validation
        semantic_start = time.perf_counter()
        semantic_result = validate_semantic(q1, q2, prediction_result)
        semantic_time = (time.perf_counter() - semantic_start) * 1000

        # Compute real confidence and trust
        adjusted_confidence = semantic_result["adjusted_confidence"]
        explanations = prediction_result.explanations or {}
        agreement = explanations.get("agreement") if isinstance(explanations, dict) else None
        uncertainty = explanations.get("uncertainty") if isinstance(explanations, dict) else None
        model_count = explanations.get("model_count", 1) if isinstance(explanations, dict) else 1

        confidence_result = compute_final_confidence(
            raw_confidence=prediction_result.confidence,
            adjusted_confidence=adjusted_confidence,
            agreement_score=agreement,
            trust_score=prediction_result.trust_score,
            uncertainty=uncertainty,
            mode=mode,
            model_count=model_count,
        )

        trust_score = compute_trust_score(
            confidence=confidence_result["final_confidence"],
            agreement=agreement,
            contradiction_count=semantic_result.get("semantic_detail", {}).get("contradiction_count", 0),
            uncertainty=uncertainty,
        )

        # Phase 3: Memory
        memory_start = time.perf_counter()
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
        memory_read_start = time.perf_counter()
        memory_entries = self._memory_manager.search("prediction:", limit=10)
        memory_read_time = (time.perf_counter() - memory_read_start) * 1000

        # Phase 4: Reflection store
        risk_level = compute_risk_level(
            trust_score=trust_score,
            confidence=confidence_result["final_confidence"],
            agreement=agreement,
            uncertainty=uncertainty,
            contradiction_count=semantic_result.get("semantic_detail", {}).get("contradiction_count", 0),
        )
        reflection_result = {
            "trust_score": trust_score,
            "trust_level": compute_trust_level(trust_score),
            "risk_level": risk_level,
            "human_review_required": trust_score < 0.4,
            "recommendations": _generate_recommendations(trust_score),
            "confidence_detail": confidence_result,
            "semantic_detail": semantic_result,
        }
        reflection_mem = self._memory_manager.store(
            key=f"reflection:{goal_obj.goal_id}",
            value=reflection_result,
            tags=["reflection", "demo"],
            agent_id="reflection",
        )
        reflection_time = (time.perf_counter() - memory_start) * 1000

        # Phase 5: Orchestration (remaining agents)
        execution_start = time.perf_counter()
        phased_agents = {"planner", "predict", "memory", "reflection"}
        remaining_agents = [a for a in agents if a not in phased_agents]
        orchestration_result = None
        if remaining_agents:
            try:
                orchestration_result = await self._orchestration_engine.run_agents(
                    agent_ids=remaining_agents,
                    input={
                        "question1": q1,
                        "question2": q2,
                        "goal_description": g,
                        "prediction": {
                            "predicted_label": prediction_result.predicted_label,
                            "prediction": prediction_result.prediction,
                            "confidence": prediction_result.confidence,
                        },
                        "result": {
                            "predicted_label": prediction_result.predicted_label,
                            "prediction": prediction_result.prediction,
                            "confidence": prediction_result.confidence,
                        },
                        "action": "full_cycle",
                        "strategy": strategy,
                        "agent_ids": agents,
                        "available_tools": tools,
                    },
                    strategy=OrchestrationStrategyType.SEQUENTIAL,
                    policies=RunPolicies(timeout_seconds=120.0, max_retries=2),
                )
            except Exception as exc:
                logger.error("Orchestration failed: %s", exc)
        execution_time = (time.perf_counter() - execution_start) * 1000
        total_time = (time.perf_counter() - overall_start) * 1000

        result = {
            "trace_id": trace_id,
            "scenario_id": scenario_id or "custom",
            "strategy": {"requested": strategy, "resolved": strategy_enum.name},
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
                "final_confidence": confidence_result["final_confidence"],
                "prob_duplicate": prediction_result.prob_duplicate,
                "prob_non_duplicate": prediction_result.prob_non_duplicate,
                "model_name": prediction_result.model_name,
                "latency_ms": prediction_result.latency_ms,
                "trust_score": trust_score,
                "trust_level": compute_trust_level(trust_score),
                "risk_level": risk_level,
            },
            "semantic_validation": semantic_result,
            "confidence_calculation": confidence_result,
            "reflection": reflection_result,
            "memory": {
                "stored": {"memory_id": mem_entry.memory_id, "key": mem_entry.key},
                "reflection_memory_id": reflection_mem.memory_id,
                "retrieved_count": len(memory_entries),
                "retrieved_entries": [
                    {"memory_id": e.memory_id, "key": e.key, "value": e.value, "tier": e.tier.name, "score": e.score}
                    for e in memory_entries
                ],
            },
            "orchestration": {
                "status": orchestration_result.status.name if orchestration_result else "skipped",
                "agent_results": [
                    {"agent_id": r.agent_id, "status": r.status.name, "processing_time_ms": r.processing_time_ms}
                    for r in (orchestration_result.agent_results if orchestration_result else [])
                ],
            }
            if orchestration_result
            else {"status": "skipped"},
            "execution_tree": plan_graph.get_execution_order(),
            "timeline": {
                "planning_time_ms": planning_time,
                "prediction_time_ms": prediction_time,
                "semantic_time_ms": semantic_time,
                "memory_write_time_ms": memory_write_time,
                "memory_read_time_ms": memory_read_time,
                "reflection_time_ms": reflection_time,
                "execution_time_ms": execution_time,
                "total_time_ms": total_time,
            },
            "explanation": generate_explanation(
                prediction=prediction_result.prediction,
                confidence=confidence_result["final_confidence"],
                model_name=prediction_result.model_name,
                question1=q1,
                question2=q2,
                agreement=agreement,
                uncertainty=uncertainty,
                trust_score=trust_score,
                risk_level=risk_level,
                semantic_penalty=semantic_result.get("semantic_penalty", semantic_result.get("adjusted_penalty", 0)),
                model_contributions=explanations.get("model_contributions", {})
                if isinstance(explanations, dict)
                else None,
                fusion_mode=(mode == "fusion"),
            ),
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
            "final_response": f"Prediction: {prediction_result.prediction} (confidence: {confidence_result['final_confidence']:.1%}, model: {prediction_result.model_name})",
        }

        self._demo_results[trace_id] = result
        return result

    async def run_multi_agent_demo(
        self,
        scenario_id: str | None = None,
        question1: str = "",
        question2: str = "",
        goal: str = "",
        strategy: str = "LINEAR",
        model_name: str | None = None,
        mode: str = "selected",
        include_reflection: bool = True,
        include_memory: bool = True,
    ) -> dict[str, Any]:
        self.initialize()
        scenario = None
        if scenario_id:
            scenario = self.get_scenario(scenario_id)

        if scenario:
            q1 = question1 or scenario["question1"]
            q2 = question2 or scenario["question2"]
            g = goal or scenario["goal"]
            model = model_name or scenario.get("model_name", "")
            mode = scenario.get("mode", mode)
        else:
            cfg = (get_config("inference") or {}).get("demo", {})
            q1 = question1
            q2 = question2
            g = goal or cfg.get("default_goal", "Analyze semantic similarity between two questions")
            model = model_name or ""

        from ares.agents.multi_agent_engine import MultiAgentEngine

        engine = MultiAgentEngine(
            agent_manager=self._agent_manager,
            agent_registry=self._agent_registry,
            tool_manager=self._tool_manager,
            memory_manager=self._memory_manager,
        )

        result = await engine.run(
            question1=q1,
            question2=q2,
            goal_description=g,
            model_name=model,
            strategy=strategy,
            mode=mode,
            scenario_id=scenario_id or "custom",
            include_reflection=include_reflection,
            include_memory=include_memory,
        )
        self._demo_results[result.get("trace_id", "multi_agent")] = result
        return result

    def get_demo_result(self, trace_id: str) -> dict[str, Any] | None:
        return self._demo_results.get(trace_id)

    def list_demo_results(self) -> list[dict[str, Any]]:
        return [
            {
                "trace_id": tid,
                "scenario_id": r.get("scenario_id"),
                "prediction": r.get("prediction", {}).get("prediction"),
                "confidence": r.get("prediction", {}).get("final_confidence"),
                "total_time_ms": r.get("timeline", {}).get("total_time_ms"),
            }
            for tid, r in self._demo_results.items()
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

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": getattr(t, "tool_id", str(i)),
                "name": getattr(t, "name", str(t)),
                "description": getattr(t, "description", ""),
            }
            for i, t in enumerate(self._tool_registry.list_all())
        ]

    def get_events(self, limit: int = 20) -> list[dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "source": e.source,
                "event_type": e.event_type,
                "data": e.data,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self._event_bus.get_events(limit=limit)
        ]

    def get_metrics(self) -> dict[str, Any]:
        return self._planning_metrics.summary()


def _generate_recommendations(trust_score: float) -> list[str]:
    if trust_score >= 0.95:
        return []
    recs = []
    if trust_score < 0.7:
        recs.append("review_manually")
    if trust_score < 0.5:
        recs.append("recheck_similarity")
    if trust_score < 0.3:
        recs.append("flag_for_expert_review")
    return recs
