from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.agent_selector import DynamicAgentSelector
from ares.agents.cache import SharedCache
from ares.agents.capability_resolver import CapabilityResolver
from ares.agents.decision_agent import DecisionAgent
from ares.agents.execution_context import ExecutionContext
from ares.agents.execution_scheduler import ExecutionScheduler
from ares.agents.failure_handler import FailureHandler
from ares.agents.manager import AgentManager
from ares.agents.observability import MultiAgentObservability
from ares.agents.registry import AgentRegistry
from ares.agents.task_decomposer import TaskDecomposer
from ares.agents.task_types import AgentTaskResult, AgentTaskSpec, AgentTaskType
from ares.agents.tool_discovery import ToolDiscovery
from ares.confidence import (
    compute_final_confidence,
    compute_risk_level,
    compute_trust_level,
    compute_trust_score,
    generate_explanation,
)
from ares.fusion import FusionEngine
from ares.inference.dispatcher import InferenceDispatcher
from ares.memory import MemoryManager
from ares.semantic_validator import validate_semantic
from ares.tools.manager import ToolManager

logger = logging.getLogger(__name__)


class MultiAgentEngine:
    def __init__(
        self,
        agent_manager: AgentManager | None = None,
        agent_registry: AgentRegistry | None = None,
        tool_manager: ToolManager | None = None,
        memory_manager: MemoryManager | None = None,
        decomposer: TaskDecomposer | None = None,
        selector: DynamicAgentSelector | None = None,
        scheduler: ExecutionScheduler | None = None,
        failure_handler: FailureHandler | None = None,
        tool_discovery: ToolDiscovery | None = None,
        observability: MultiAgentObservability | None = None,
        cache: SharedCache | None = None,
    ) -> None:
        self._agent_manager = agent_manager or AgentManager()
        self._agent_registry = agent_registry or AgentRegistry()
        self._tool_manager = tool_manager
        self._memory_manager = memory_manager
        self._decomposer = decomposer or TaskDecomposer()
        self._selector = selector or DynamicAgentSelector(registry=self._agent_registry)
        self._resolver = CapabilityResolver()
        self._scheduler = scheduler or ExecutionScheduler(agent_manager=self._agent_manager)
        self._failure_handler = failure_handler or FailureHandler()
        self._tool_discovery = tool_discovery or ToolDiscovery(manager=self._tool_manager)
        self._observability = observability or MultiAgentObservability()
        self._cache = cache or SharedCache()
        self._decision_agent = DecisionAgent()

    @property
    def decomposer(self) -> TaskDecomposer:
        return self._decomposer

    @property
    def selector(self) -> DynamicAgentSelector:
        return self._selector

    def _resolve_model(self, model_name: str) -> str:
        if model_name:
            return model_name
        models = InferenceDispatcher.list_models()
        return models[0] if models else ""

    async def _predict_phase(
        self, ctx: ExecutionContext, question1: str, question2: str, model_name: str, mode: str = "selected"
    ) -> None:
        try:
            from ares.orchestration.prediction_service import get_prediction_service

            resolved = self._resolve_model(model_name)
            service = get_prediction_service()
            prediction_result = service.predict_raw(
                question1,
                question2,
                model=resolved,
                reflect=False,
            )
            ctx.phase_results["raw_prediction"] = (
                prediction_result.to_dict()
                if hasattr(prediction_result, "to_dict")
                else {
                    "predicted_label": prediction_result.predicted_label,
                    "prediction": prediction_result.prediction,
                    "confidence": prediction_result.confidence,
                    "prob_duplicate": prediction_result.prob_duplicate,
                    "prob_non_duplicate": prediction_result.prob_non_duplicate,
                    "model_name": prediction_result.model_name,
                    "selected_model": resolved,
                    "executed_model": prediction_result.executed_model,
                    "backend": prediction_result.backend,
                    "latency_ms": prediction_result.latency_ms,
                    "trust_score": prediction_result.trust_score,
                    "trust_level": prediction_result.trust_level,
                    "risk_level": prediction_result.risk_level,
                    "human_review_required": prediction_result.human_review_required,
                    "recommendations": prediction_result.recommendations,
                    "explanations": prediction_result.explanations,
                }
            )
            ctx.set("_prediction_result", ctx.phase_results["raw_prediction"])
            ctx.set("_executed_model", resolved)
        except Exception as e:
            logger.exception("Prediction phase failed")
            ctx.phase_results["raw_prediction"] = {"error": str(e)}

    def _semantic_phase(self, ctx: ExecutionContext, question1: str, question2: str) -> None:
        raw = ctx.phase_results.get("raw_prediction", {})
        if not raw or "error" in raw:
            return
        try:
            from ares._result import PredictionResult

            pr = PredictionResult(
                predicted_label=raw.get("predicted_label", 0),
                prediction=raw.get("prediction", "unknown"),
                confidence=raw.get("confidence", 0.0),
                prob_duplicate=raw.get("prob_duplicate", 0.0),
                prob_non_duplicate=raw.get("prob_non_duplicate", 0.0),
                model_name=raw.get("model_name", ""),
                latency_ms=raw.get("latency_ms", 0.0),
            )
            semantic_result = validate_semantic(question1, question2, pr)
            ctx.phase_results["semantic_validation"] = semantic_result
            adjusted = semantic_result.get("adjusted_confidence", raw["confidence"])
            ctx.set("_adjusted_confidence", adjusted)
        except Exception as e:
            logger.warning("Semantic validation failed: %s", e)
            ctx.phase_results["semantic_validation"] = {"error": str(e)}

    def _fusion_phase(self, ctx: ExecutionContext, question1: str, question2: str, mode: str) -> None:
        if mode != "fusion":
            return
        try:
            raw_pred = ctx.phase_results.get("raw_prediction", {})
            explanations = raw_pred.get("explanations", {})
            contributions = explanations.get("model_contributions", {})
            if contributions:
                results = []
                for name, data in contributions.items():
                    results.append(
                        {
                            "model_name": name,
                            "predicted_label": data.get("predicted_label", 0),
                            "confidence": data.get("confidence", 0.0),
                            "prob_duplicate": data.get("prob_duplicate", 0.5),
                            "latency_ms": data.get("latency_ms", 0.0),
                        }
                    )
                engine = FusionEngine()
                ctx.phase_results["fusion"] = {
                    "models": results,
                    "model_count": explanations.get("model_count", len(results)),
                    "agreement": explanations.get("agreement", engine._compute_agreement(results)),
                    "uncertainty": explanations.get("uncertainty", engine._compute_uncertainty(results)),
                }
                ctx.set("_fusion_results", results)
            else:
                logger.debug("No fusion contributions found in prediction result")
        except Exception as e:
            logger.warning("Fusion phase failed: %s", e)

    def _memory_phase(self, ctx: ExecutionContext) -> None:
        raw = ctx.phase_results.get("raw_prediction", {})
        if not self._memory_manager or not raw or "error" in raw:
            return
        try:
            mem_entry = self._memory_manager.store(
                key=f"prediction:{ctx.trace_id}", value=raw, tags=["prediction", "multi-agent"], agent_id="predict"
            )
            ctx.phase_results["memory_store"] = {"memory_id": mem_entry.memory_id}
        except Exception as e:
            logger.warning("Memory store failed: %s", e)

    def _reflection_phase(self, ctx: ExecutionContext) -> dict[str, Any]:
        raw = ctx.phase_results.get("raw_prediction", {})
        if not raw or "error" in raw:
            return {}
        try:
            adjusted = ctx.get("_adjusted_confidence", raw.get("confidence", 0.0))
            fusion = ctx.phase_results.get("fusion", {})
            agreement = fusion.get("agreement")
            uncertainty = fusion.get("uncertainty")
            model_count = fusion.get("model_count", 1)

            semantic_data = ctx.phase_results.get("semantic_validation", {})
            semantic_detail = semantic_data.get("semantic_detail", {}) if isinstance(semantic_data, dict) else {}
            contradiction_count = semantic_detail.get("contradiction_count", 0)

            conf_result = compute_final_confidence(
                raw_confidence=raw.get("confidence", 0.0),
                adjusted_confidence=adjusted,
                agreement_score=agreement,
                trust_score=raw.get("trust_score"),
                uncertainty=uncertainty,
                model_count=model_count,
            )

            trust_score = compute_trust_score(
                confidence=conf_result["final_confidence"],
                agreement=agreement,
                contradiction_count=contradiction_count,
                uncertainty=uncertainty,
            )

            risk_level = compute_risk_level(
                trust_score=trust_score,
                confidence=conf_result["final_confidence"],
                agreement=agreement,
                uncertainty=uncertainty,
                contradiction_count=contradiction_count,
            )

            recommendations = []
            if trust_score < 0.7:
                recommendations.append("review_manually")
            if trust_score < 0.5:
                recommendations.append("recheck_similarity")
            if trust_score < 0.3:
                recommendations.append("flag_for_expert_review")

            reflection_result = {
                "trust_score": trust_score,
                "trust_level": compute_trust_level(trust_score),
                "risk_level": risk_level,
                "human_review_required": trust_score < 0.4,
                "recommendations": recommendations,
                "confidence_detail": conf_result,
            }
            ctx.set("reflection_result", reflection_result)
            if self._memory_manager:
                from contextlib import suppress

                with suppress(Exception):
                    self._memory_manager.store(
                        key=f"reflection:{ctx.trace_id}",
                        value=reflection_result,
                        tags=["reflection", "multi-agent"],
                        agent_id="reflection",
                    )
            return reflection_result
        except Exception as e:
            logger.warning("Reflection failed: %s", e)
            return {"error": str(e), "fallback": True}

    async def _decision_phase(self, ctx: ExecutionContext) -> Any:
        return await self._decision_agent.execute(
            {
                "task_results": {
                    AgentTaskType.PREDICT.name: {
                        "task_id": "predict_task",
                        "success": "error" not in ctx.phase_results.get("raw_prediction", {}),
                        "output": ctx.phase_results.get("raw_prediction", {}),
                        "agent_id": "predict",
                        "confidence": ctx.phase_results.get("raw_prediction", {}).get("confidence", 0.0),
                    },
                    AgentTaskType.SEMANTIC_VALIDATE.name: {
                        "task_id": "semantic_task",
                        "success": "error" not in ctx.phase_results.get("semantic_validation", {}),
                        "output": ctx.phase_results.get("semantic_validation", {}),
                        "agent_id": "semantic_validator",
                        "confidence": ctx.phase_results.get("semantic_validation", {}).get("adjusted_confidence", 0.0),
                    },
                    AgentTaskType.REFLECT.name: {
                        "task_id": "reflect_task",
                        "success": "error" not in ctx.phase_results.get("reflection", {}),
                        "output": ctx.phase_results.get("reflection", {}),
                        "agent_id": "reflection",
                        "confidence": ctx.phase_results.get("reflection", {}).get("trust_score", 0.0),
                    },
                },
                "prediction": ctx.phase_results.get("raw_prediction", {}),
                "reflection": ctx.phase_results.get("reflection", {}),
                "semantic_validation": ctx.phase_results.get("semantic_validation", {}),
            }
        )

    async def run(
        self,
        question1: str,
        question2: str,
        goal_description: str = "",
        model_name: str = "",
        strategy: str = "LINEAR",
        threshold: float = 0.5,
        scenario_id: str = "custom",
        include_reflection: bool = True,
        include_memory: bool = True,
        mode: str = "selected",
    ) -> dict[str, Any]:
        self._observability.start_tracking()
        overall_start = time.perf_counter()
        resolved_model = self._resolve_model(model_name)

        ctx = ExecutionContext(
            question1=question1,
            question2=question2,
            goal_description=goal_description or "Analyze semantic similarity between two questions",
            model_name=resolved_model,
            strategy=strategy,
            threshold=threshold,
            scenario_id=scenario_id,
        )

        logger.info("MultiAgentEngine starting (trace=%s, model=%s, mode=%s)", ctx.trace_id, resolved_model, mode)

        ctx.start_phase("decomposition")
        try:
            decomp = self._decomposer.decompose(
                ctx.goal_description, include_reflection=include_reflection, include_memory=include_memory
            )
            decomp = self._selector.select_for_decomposition(decomp)
        except Exception as e:
            logger.exception("Task decomposition failed")
            return self._build_error_result(ctx, f"Decomposition failed: {e}", overall_start)
        ctx.end_phase("decomposition")

        ctx.start_phase("fusion" if mode == "fusion" else "prediction")
        pred_spec = AgentTaskSpec(
            task_id="predict_task",
            task_type=AgentTaskType.PREDICT,
            agent_id="predict",
            description="Generate duplicate prediction using inference engine",
        )
        self._observability.record_task_start(pred_spec)
        await self._predict_phase(ctx, question1, question2, model_name, mode=mode)
        raw_pred = ctx.phase_results.get("raw_prediction", {})
        pred_success = "error" not in raw_pred
        pred_result = AgentTaskResult(
            task_id="predict_task",
            task_type=AgentTaskType.PREDICT,
            agent_id="predict",
            success=pred_success,
            output=raw_pred,
            confidence=raw_pred.get("confidence", 0.0),
        )
        self._observability.record_task_end(pred_spec, pred_result)
        ctx.add_task_result(pred_result)

        if mode == "fusion":
            self._fusion_phase(ctx, question1, question2, mode)
        ctx.end_phase("fusion" if mode == "fusion" else "prediction")

        ctx.start_phase("semantic_validation")
        sem_spec = AgentTaskSpec(
            task_id="semantic_task",
            task_type=AgentTaskType.SEMANTIC_VALIDATE,
            agent_id="semantic_validator",
            description="Validate prediction for semantic consistency",
            depends_on=["predict_task"],
        )
        self._observability.record_task_start(sem_spec)
        self._semantic_phase(ctx, question1, question2)
        sem_result_data = ctx.phase_results.get("semantic_validation", {})
        sem_success = "error" not in sem_result_data
        sem_result = AgentTaskResult(
            task_id="semantic_task",
            task_type=AgentTaskType.SEMANTIC_VALIDATE,
            agent_id="semantic_validator",
            success=sem_success,
            output=sem_result_data,
            confidence=sem_result_data.get("adjusted_confidence", 0.0),
        )
        self._observability.record_task_end(sem_spec, sem_result)
        ctx.add_task_result(sem_result)
        ctx.end_phase("semantic_validation")

        if include_memory:
            ctx.start_phase("memory")
            mem_spec = AgentTaskSpec(
                task_id="memory_task",
                task_type=AgentTaskType.MEMORY_STORE,
                agent_id="memory",
                description="Store prediction result in memory",
                depends_on=["predict_task"],
            )
            self._observability.record_task_start(mem_spec)
            self._memory_phase(ctx)
            mem_success = "memory_store" in ctx.phase_results
            mem_result = AgentTaskResult(
                task_id="memory_task",
                task_type=AgentTaskType.MEMORY_STORE,
                agent_id="memory",
                success=mem_success,
                output=ctx.phase_results.get("memory_store", {}),
            )
            self._observability.record_task_end(mem_spec, mem_result)
            ctx.add_task_result(mem_result)
            ctx.end_phase("memory")

        ctx.start_phase("reflection")
        reflection_result = {}
        if include_reflection:
            ref_spec = AgentTaskSpec(
                task_id="reflect_task",
                task_type=AgentTaskType.REFLECT,
                agent_id="reflection",
                description="Reflect on prediction to assess trust and risk",
                depends_on=["predict_task", "semantic_task"],
            )
            self._observability.record_task_start(ref_spec)
            reflection_result = self._reflection_phase(ctx)
            ctx.phase_results["reflection"] = reflection_result
            ref_success = "error" not in reflection_result
            ref_result = AgentTaskResult(
                task_id="reflect_task",
                task_type=AgentTaskType.REFLECT,
                agent_id="reflection",
                success=ref_success,
                output=reflection_result,
                confidence=reflection_result.get("trust_score", 0.0),
            )
            self._observability.record_task_end(ref_spec, ref_result)
            ctx.add_task_result(ref_result)
        ctx.end_phase("reflection")

        ctx.start_phase("decision")
        dec_spec = AgentTaskSpec(
            task_id="decision_task",
            task_type=AgentTaskType.DECIDE,
            agent_id="decision_agent",
            description="Aggregate all signals into final decision",
            depends_on=["predict_task", "semantic_task", "reflect_task"]
            if include_reflection
            else ["predict_task", "semantic_task"],
        )
        self._observability.record_task_start(dec_spec)
        decision_output = await self._decision_phase(ctx)
        ctx.phase_results["decision"] = decision_output.result if decision_output else {}
        dec_success = decision_output is not None and decision_output.status.name == "SUCCESS"
        dec_result = AgentTaskResult(
            task_id="decision_task",
            task_type=AgentTaskType.DECIDE,
            agent_id="decision_agent",
            success=dec_success,
            output=ctx.phase_results.get("decision", {}),
            confidence=decision_output.confidence if decision_output else 0.0,
        )
        self._observability.record_task_end(dec_spec, dec_result)
        ctx.add_task_result(dec_result)
        ctx.end_phase("decision")

        ctx.mark_completed()
        total_ms = (time.perf_counter() - overall_start) * 1000
        agent_summary = self._selector.available_agents_summary()
        tool_summary = self._tool_discovery.list_discoverable_tools()

        ref_result = ctx.phase_results.get("reflection", {})
        conf_detail = ref_result.get("confidence_detail", {}) if isinstance(ref_result, dict) else {}
        raw_pred = ctx.phase_results.get("raw_prediction", {})
        sem_valid = ctx.phase_results.get("semantic_validation", {})

        if not conf_detail:
            conf_detail = {
                "raw_confidence": raw_pred.get("confidence", 0.0),
                "adjusted_confidence": sem_valid.get("adjusted_confidence", raw_pred.get("confidence", 0.0)),
                "trust_score": ref_result.get("trust_score", raw_pred.get("trust_score")),
                "final_confidence": decision_output.confidence if decision_output else raw_pred.get("confidence", 0.0),
                "mode": mode,
            }

        decision_result = decision_output.result if decision_output else {}
        prediction_label = decision_result.get("prediction", raw_pred.get("prediction", "unknown"))
        final_confidence = conf_detail.get("final_confidence", 0.0)
        model_used = raw_pred.get("model_name", ctx.model_name or "")

        explanation = generate_explanation(
            prediction=prediction_label,
            confidence=final_confidence,
            model_name=model_used,
            question1=ctx.question1,
            question2=ctx.question2,
            agreement=ctx.phase_results.get("fusion", {}).get("agreement"),
            uncertainty=ctx.phase_results.get("fusion", {}).get("uncertainty"),
            trust_score=conf_detail.get("trust_score"),
            risk_level=ref_result.get("risk_level"),
            semantic_penalty=sem_valid.get("semantic_penalty", 0.0),
            fusion_mode=(mode == "fusion"),
        )

        result = {
            "multi_agent": True,
            "trace_id": ctx.trace_id,
            "scenario_id": ctx.scenario_id,
            "status": "completed",
            "mode": mode,
            "total_time_ms": total_ms,
            "goal": {"description": ctx.goal_description, "strategy": ctx.strategy},
            "input": {"question1": ctx.question1, "question2": ctx.question2, "model": ctx.model_name},
            "decomposition": {
                "task_count": len(decomp.tasks),
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "task_type": t.task_type.name,
                        "agent_id": t.agent_id,
                        "depends_on": t.depends_on,
                    }
                    for t in decomp.tasks
                ],
                "parallel_groups": decomp.parallel_groups,
            },
            "prediction": ctx.phase_results.get("raw_prediction", {}),
            "fusion": ctx.phase_results.get("fusion", {}),
            "semantic_validation": ctx.phase_results.get("semantic_validation", {}),
            "confidence_calculation": conf_detail,
            "reflection": ctx.phase_results.get("reflection", {}),
            "decision": decision_result,
            "decision_confidence": decision_output.confidence if decision_output else 0.0,
            "explanation": explanation,
            "final_response": self._build_final_response(decision_output, ctx),
            "agent_selection": agent_summary,
            "tool_discovery": tool_summary,
            "execution_dag": self._observability.execution_dag(),
            "agent_timeline": self._observability.agent_timeline(),
            "timeline": {
                "decomposition_ms": ctx.phase_timings.get("decomposition_ms", 0),
                "prediction_ms": ctx.phase_timings.get("prediction_ms", ctx.phase_timings.get("fusion_ms", 0)),
                "semantic_validation_ms": ctx.phase_timings.get("semantic_validation_ms", 0),
                "memory_ms": ctx.phase_timings.get("memory_ms", 0),
                "reflection_ms": ctx.phase_timings.get("reflection_ms", 0),
                "decision_ms": ctx.phase_timings.get("decision_ms", 0),
                "total_ms": total_ms,
            },
            "observability": self._observability.summary(),
            "cache_stats": self._cache.stats(),
        }
        return result

    def _build_final_response(self, decision_output: Any, ctx: ExecutionContext) -> str:
        if decision_output is None or decision_output.status.name != "SUCCESS":
            raw = ctx.phase_results.get("raw_prediction", {})
            conf = raw.get("confidence", 0.0)
            pred = raw.get("prediction", "unknown")
            return f"Prediction: {pred} (confidence: {conf:.2%})"
        decision = decision_output.result or {}
        prediction = decision.get("prediction", "unknown")
        final_conf = decision.get("final_confidence", 0.0)
        model = decision.get("model_name", ctx.get("_executed_model", ctx.model_name or "unknown"))
        return f"Decision: {prediction} (confidence: {final_conf:.2%}, model: {model})"

    def _build_error_result(self, ctx: ExecutionContext, error: str, start_time: float) -> dict[str, Any]:
        elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "multi_agent": True,
            "trace_id": ctx.trace_id,
            "status": "error",
            "error": error,
            "total_time_ms": elapsed,
        }
