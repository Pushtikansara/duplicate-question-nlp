from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from duplicate_question_app._integration.integration_configuration import IntegrationConfig
from duplicate_question_app._integration.lifecycle import LifecycleManager, ModuleState
from duplicate_question_app._integration.pipeline_context import PipelineContext
from duplicate_question_app._integration.pipeline_events import PipelineEvent
from duplicate_question_app._integration.pipeline_hooks import PipelineHook
from duplicate_question_app._integration.pipeline_result import PipelineExecutionMetadata, PipelineResult

logger = logging.getLogger(__name__)

MODULE_NAMES = ["perception", "routing", "memory_read", "semantic", "reasoning", "debate", "decision", "memory_write"]


class CognitivePipeline:
    def __init__(
        self,
        config: IntegrationConfig | None = None,
        hook: PipelineHook | None = None,
        lifecycle: LifecycleManager | None = None,
        memory_manager: Any = None,
        perception_pipeline: Any = None,
        routing_engine: Any = None,
        semantic_service: Any = None,
        reasoning_engine: Any = None,
        debate_engine: Any = None,
        plugins: list[Any] | None = None,
    ) -> None:
        self.config = config or IntegrationConfig()
        self.hook = hook or PipelineHook()
        self.lifecycle = lifecycle or LifecycleManager()
        self._memory_manager = memory_manager
        self._perception_pipeline = perception_pipeline
        self._routing_engine = routing_engine
        self._semantic_service = semantic_service
        self._reasoning_engine = reasoning_engine
        self._debate_engine = debate_engine
        self._plugins = plugins or []

        for module_name in MODULE_NAMES:
            self.lifecycle.register(module_name)

    def run(
        self,
        question_a: str,
        question_b: str,
        prediction_fn: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> PipelineResult:
        start_time = time.perf_counter()
        started_at = datetime.now().isoformat()
        errors: list[str] = []
        metadata = PipelineExecutionMetadata()
        context_dict: dict[str, Any] = {
            "question_a": question_a,
            "question_b": question_b,
            "started_at": started_at,
        }

        self._publish(PipelineEvent.PIPELINE_STARTED, context_dict)

        # ---- 1. Perception ----
        perception_output = None
        if self.config.enable_perception and self._perception_pipeline is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_PERCEPTION, context_dict)
                self.lifecycle.set_state("perception", ModuleState.RUNNING)
                perception_output = self._perception_pipeline.run(question_a)
                context_dict["perception_result"] = perception_output
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["perception"] = lat
                self.lifecycle.set_latency("perception", lat)
                self.lifecycle.set_state("perception", ModuleState.COMPLETED)
                self._publish(PipelineEvent.AFTER_PERCEPTION, context_dict)
                metadata.modules_executed.append("perception")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Perception failed: %s", e)
                self.lifecycle.set_state("perception", ModuleState.FAILED)
                self.lifecycle.set_error("perception", str(e))
                self.lifecycle.set_latency("perception", lat)
                if self.config.fail_on_perception_error:
                    raise
                errors.append(f"perception: {e}")
        else:
            metadata.modules_skipped.append("perception")

        # ---- 2. Routing ----
        routing_result = None
        if self.config.enable_routing and self._routing_engine is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_ROUTING, context_dict)
                self.lifecycle.set_state("routing", ModuleState.RUNNING)
                routing_result = self._routing_engine.route(
                    question_a=question_a,
                    question_b=question_b,
                    cross_encoder_score=None,
                )
                context_dict["routing_result"] = routing_result
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["routing"] = lat
                metadata.routing_choice = getattr(routing_result, "selected_pipeline", "")
                self.lifecycle.set_latency("routing", lat)
                self.lifecycle.set_state("routing", ModuleState.COMPLETED)
                self._publish(PipelineEvent.AFTER_ROUTING, context_dict)
                metadata.modules_executed.append("routing")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Routing failed: %s", e)
                self.lifecycle.set_state("routing", ModuleState.FAILED)
                self.lifecycle.set_error("routing", str(e))
                self.lifecycle.set_latency("routing", lat)
                if self.config.fail_on_routing_error:
                    raise
                errors.append(f"routing: {e}")
        else:
            metadata.modules_skipped.append("routing")

        # ---- 3. Memory Read ----
        retrieved_memories: list[Any] = []
        if self.config.enable_memory_read and self._memory_manager is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_MEMORY_READ, context_dict)
                self.lifecycle.set_state("memory_read", ModuleState.RUNNING)
                from duplicate_question_app._memory.interfaces import MemoryQuery

                query = MemoryQuery(
                    text=f"{question_a} {question_b}",
                    min_confidence=self.config.memory_min_confidence,
                    limit=self.config.memory_read_limit,
                )
                memory_result = self._memory_manager.search(query)
                if memory_result is not None:
                    retrieved_memories = getattr(memory_result, "entries", [])
                    metadata.memory_hits = len(retrieved_memories)
                else:
                    metadata.memory_misses = 1
                context_dict["retrieved_memories"] = retrieved_memories
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["memory_read"] = lat
                self.lifecycle.set_latency("memory_read", lat)
                self.lifecycle.set_state("memory_read", ModuleState.COMPLETED)
                self._publish(PipelineEvent.AFTER_MEMORY_READ, context_dict)
                metadata.modules_executed.append("memory_read")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Memory read failed: %s", e)
                self.lifecycle.set_state("memory_read", ModuleState.FAILED)
                self.lifecycle.set_error("memory_read", str(e))
                self.lifecycle.set_latency("memory_read", lat)
                if self.config.fail_on_memory_error:
                    raise
                errors.append(f"memory_read: {e}")
        else:
            metadata.modules_skipped.append("memory_read")

        # ---- 4. Semantic ----
        semantic_assessment = None
        if self.config.enable_semantic and self._semantic_service is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_SEMANTIC, context_dict)
                self.lifecycle.set_state("semantic", ModuleState.RUNNING)
                semantic_assessment, semantic_meta = self._semantic_service.assess(
                    question_a, question_b, use_cache=False
                )
                context_dict["semantic_assessment"] = semantic_assessment
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["semantic"] = lat
                self.lifecycle.set_latency("semantic", lat)
                self.lifecycle.set_state("semantic", ModuleState.COMPLETED)
                self._publish(PipelineEvent.AFTER_SEMANTIC, context_dict)
                metadata.modules_executed.append("semantic")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Semantic failed: %s", e)
                self.lifecycle.set_state("semantic", ModuleState.FAILED)
                self.lifecycle.set_error("semantic", str(e))
                self.lifecycle.set_latency("semantic", lat)
                if self.config.fail_on_semantic_error:
                    raise
                errors.append(f"semantic: {e}")
        else:
            metadata.modules_skipped.append("semantic")

        # ---- 5. Reasoning ----
        reasoning_result = None
        if self.config.enable_reasoning and self._reasoning_engine is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_REASONING, context_dict)
                self.lifecycle.set_state("reasoning", ModuleState.RUNNING)
                reasoning_result = self._reasoning_engine.reason(
                    rep_a=None,
                    rep_b=None,
                    assessment=semantic_assessment,
                    cross_encoder_score=None,
                )
                context_dict["reasoning_result"] = reasoning_result
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["reasoning"] = lat
                self.lifecycle.set_latency("reasoning", lat)
                self.lifecycle.set_state("reasoning", ModuleState.COMPLETED)
                metadata.confidence = getattr(reasoning_result, "confidence", 0.0)
                metadata.reasoning_depth = getattr(reasoning_result, "decision", "")
                self._publish(PipelineEvent.AFTER_REASONING, context_dict)
                metadata.modules_executed.append("reasoning")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Reasoning failed: %s", e)
                self.lifecycle.set_state("reasoning", ModuleState.FAILED)
                self.lifecycle.set_error("reasoning", str(e))
                self.lifecycle.set_latency("reasoning", lat)
                if self.config.fail_on_reasoning_error:
                    raise
                errors.append(f"reasoning: {e}")
        else:
            metadata.modules_skipped.append("reasoning")

        # ---- 6. MADE Debate ----
        debate_result = None
        if self.config.enable_debate and self._debate_engine is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_DEBATE, context_dict)
                self.lifecycle.set_state("debate", ModuleState.RUNNING)
                debate_result = self._debate_engine.debate(
                    rep_a=None,
                    rep_b=None,
                    assessment=semantic_assessment,
                    reasoning_result=reasoning_result,
                )
                context_dict["debate_result"] = debate_result
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["debate"] = lat
                self.lifecycle.set_latency("debate", lat)
                self.lifecycle.set_state("debate", ModuleState.COMPLETED)
                agents_used = getattr(debate_result, "agents_used", [])
                metadata.debate_participation = len(agents_used) if agents_used else 0
                self._publish(PipelineEvent.AFTER_DEBATE, context_dict)
                metadata.modules_executed.append("debate")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Debate failed: %s", e)
                self.lifecycle.set_state("debate", ModuleState.FAILED)
                self.lifecycle.set_error("debate", str(e))
                self.lifecycle.set_latency("debate", lat)
                if self.config.fail_on_debate_error:
                    raise
                errors.append(f"debate: {e}")
        else:
            metadata.modules_skipped.append("debate")

        # ---- 7. Final Decision ----
        prediction = {}
        t0 = time.perf_counter()
        try:
            self._publish(PipelineEvent.BEFORE_DECISION, context_dict)
            self.lifecycle.set_state("decision", ModuleState.RUNNING)
            if prediction_fn is not None:
                prediction = prediction_fn(question_a, question_b)
            context_dict["prediction_result"] = prediction
            lat = (time.perf_counter() - t0) * 1000
            metadata.module_latencies["decision"] = lat
            metadata.confidence = prediction.get("confidence", metadata.confidence)
            self.lifecycle.set_latency("decision", lat)
            self.lifecycle.set_state("decision", ModuleState.COMPLETED)
            self._publish(PipelineEvent.AFTER_DECISION, context_dict)
            metadata.modules_executed.append("decision")
        except Exception as e:
            lat = (time.perf_counter() - t0) * 1000
            logger.error("Decision failed: %s", e)
            self.lifecycle.set_state("decision", ModuleState.FAILED)
            self.lifecycle.set_error("decision", str(e))
            self.lifecycle.set_latency("decision", lat)
            errors.append(f"decision: {e}")

        # ---- 8. Memory Write ----
        if self.config.enable_memory_write and self._memory_manager is not None:
            t0 = time.perf_counter()
            try:
                self._publish(PipelineEvent.BEFORE_MEMORY_WRITE, context_dict)
                self.lifecycle.set_state("memory_write", ModuleState.RUNNING)
                self._store_all_memories(
                    question_a,
                    question_b,
                    prediction,
                    routing_result,
                    semantic_assessment,
                    reasoning_result,
                    debate_result,
                    metadata,
                )
                lat = (time.perf_counter() - t0) * 1000
                metadata.module_latencies["memory_write"] = lat
                self.lifecycle.set_latency("memory_write", lat)
                self.lifecycle.set_state("memory_write", ModuleState.COMPLETED)
                self._publish(PipelineEvent.AFTER_MEMORY_WRITE, context_dict)
                metadata.modules_executed.append("memory_write")
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                logger.warning("Memory write failed: %s", e)
                self.lifecycle.set_state("memory_write", ModuleState.FAILED)
                self.lifecycle.set_error("memory_write", str(e))
                self.lifecycle.set_latency("memory_write", lat)
                if self.config.fail_on_memory_error:
                    raise
                errors.append(f"memory_write: {e}")
        else:
            metadata.modules_skipped.append("memory_write")

        # ---- Complete ----
        total_latency = (time.perf_counter() - start_time) * 1000
        metadata.total_latency_ms = total_latency
        completed_at = datetime.now().isoformat()

        context = PipelineContext(
            question_a=question_a,
            question_b=question_b,
            perception_result=perception_output,
            routing_result=routing_result,
            retrieved_memories=retrieved_memories,
            semantic_assessment=semantic_assessment,
            reasoning_result=reasoning_result,
            debate_result=debate_result,
            prediction_result=prediction,
            started_at=started_at,
            completed_at=completed_at,
        )

        success = len(errors) == 0 or not self._is_fatal_error(errors)
        result = PipelineResult(
            success=success,
            context=context,
            prediction=prediction,
            metadata=metadata,
            error="; ".join(errors) if errors else None,
        )

        if success:
            self._publish(PipelineEvent.PIPELINE_COMPLETED, context_dict)
        else:
            self._publish(PipelineEvent.PIPELINE_FAILED, context_dict)

        for plugin in self._plugins:
            try:
                plugin.after_pipeline(result)
            except Exception as e:
                logger.warning("Plugin after_pipeline failed: %s", e)

        return result

    def _store_all_memories(
        self,
        question_a: str,
        question_b: str,
        prediction: dict[str, Any],
        routing_result: Any,
        semantic_assessment: Any,
        reasoning_result: Any,
        debate_result: Any,
        metadata: PipelineExecutionMetadata,
    ) -> None:
        if self._memory_manager is None:
            return

        confidence = prediction.get("confidence", 0.0)
        decision = prediction.get("prediction", "unknown")
        latency_ms = prediction.get("latency_ms", 0.0)
        pipeline_used = metadata.routing_choice or "full"
        prob_dup = prediction.get("prob_duplicate", 0.5)

        try:
            self._memory_manager.store_episodic(
                question_a=question_a,
                question_b=question_b,
                pipeline_used=pipeline_used,
                decision=decision,
                confidence=confidence,
                latency_ms=latency_ms,
                metadata={"prob_duplicate": prob_dup},
            )
        except Exception as e:
            logger.warning("Failed to store episodic memory: %s", e)

        try:
            self._memory_manager.store_performance(
                latency_ms=metadata.total_latency_ms,
                pipeline_cost=0.0,
                routing_decision=pipeline_used,
                memory_hit_rate=metadata.memory_hits / max(metadata.memory_hits + metadata.memory_misses, 1),
                execution_metrics=metadata.module_latencies,
            )
        except Exception as e:
            logger.warning("Failed to store performance memory: %s", e)

        if reasoning_result is not None:
            try:
                reasoning_graph = getattr(reasoning_result, "reasoning_graph", {})
                premises_list = getattr(reasoning_result, "premises", [])
                evidence_list = getattr(reasoning_result, "supporting_evidence", [])
                hypotheses_list = getattr(reasoning_result, "hypotheses", [])
                confidence_chain = getattr(reasoning_result, "confidence_chain", {})
                reasoning_trace = getattr(reasoning_result, "reasoning_trace", {})

                premises_dicts = [p if isinstance(p, dict) else {"text": str(p)} for p in premises_list]
                evidence_dicts = [e if isinstance(e, dict) else {"text": str(e)} for e in evidence_list]
                hypothesis_dicts = [h if isinstance(h, dict) else {"text": str(h)} for h in hypotheses_list]

                self._memory_manager.store_reasoning(
                    reasoning_graph={"graph": str(reasoning_graph)},
                    premises=premises_dicts,
                    evidence_chains=evidence_dicts,
                    hypotheses=hypothesis_dicts,
                    confidence_chain={"confidence": confidence_chain}
                    if not isinstance(confidence_chain, dict)
                    else confidence_chain,
                    reasoning_trace={"trace": str(reasoning_trace)}
                    if not isinstance(reasoning_trace, dict)
                    else reasoning_trace,
                )
            except Exception as e:
                logger.warning("Failed to store reasoning memory: %s", e)

        if debate_result is not None:
            try:
                agent_results = getattr(debate_result, "agent_results", [])
                votes = getattr(debate_result, "votes", [])
                conflicts = getattr(debate_result, "conflict_reports", [])
                consensus = getattr(debate_result, "consensus", None)

                agent_dicts = [a.to_dict() if hasattr(a, "to_dict") else {"name": str(a)} for a in agent_results]
                vote_dicts = [v.to_dict() if hasattr(v, "to_dict") else {"agent": str(v)} for v in votes]
                conflict_dicts = [c.to_dict() if hasattr(c, "to_dict") else {"type": str(c)} for c in conflicts]
                consensus_dict = consensus.to_dict() if hasattr(consensus, "to_dict") and consensus else {}
                disagreements_list = getattr(debate_result, "debate_summary", "")
                confidence_dist = getattr(consensus, "confidence", confidence) if consensus else confidence

                self._memory_manager.store_debate(
                    agent_results=agent_dicts,
                    votes=vote_dicts,
                    conflicts=conflict_dicts,
                    consensus=consensus_dict,
                    disagreements=[disagreements_list] if disagreements_list else [],
                    confidence_distribution={"final": confidence_dist},
                )
            except Exception as e:
                logger.warning("Failed to store debate memory: %s", e)

        if semantic_assessment is not None:
            try:
                concepts = getattr(semantic_assessment, "concept_overlap", None)
                entities = getattr(semantic_assessment, "entity_overlap", None)
                relations = getattr(semantic_assessment, "relation_similarity", None)
                intent = getattr(semantic_assessment, "intent_similarity", None)

                self._memory_manager.store_semantic(
                    concepts=[{"overlap": str(concepts)}] if concepts else [],
                    entities=[{"overlap": str(entities)}] if entities else [],
                    relations=[{"similarity": str(relations)}] if relations else [],
                    intent_pattern=str(intent) if intent else "",
                )
            except Exception as e:
                logger.warning("Failed to store semantic memory: %s", e)

    def _publish(self, event: PipelineEvent, context: dict[str, Any]) -> None:
        if self.config.enable_hooks:
            try:
                self.hook.publish(event, context)
            except Exception as e:
                logger.warning("Hook publish failed for %s: %s", event, e)

    def _is_fatal_error(self, errors: list[str]) -> bool:
        fatal_prefixes = ["decision"]
        for error in errors:
            for prefix in fatal_prefixes:
                if error.startswith(prefix):
                    return True
        return False
