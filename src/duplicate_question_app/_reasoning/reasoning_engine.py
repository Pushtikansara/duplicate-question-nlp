from __future__ import annotations

import time

from duplicate_question_app._reasoning.confidence_reasoner import DefaultConfidenceReasoner
from duplicate_question_app._reasoning.conflict_resolver import DefaultConflictResolver
from duplicate_question_app._reasoning.decision_reasoner import DefaultDecisionReasoner
from duplicate_question_app._reasoning.evidence_chain import DefaultEvidenceChain
from duplicate_question_app._reasoning.hypothesis_generator import DefaultHypothesisGenerator
from duplicate_question_app._reasoning.interfaces import (
    ConfidenceReasoner,
    ConflictResolver,
    DecisionReasoner,
    EvidenceChain,
    HypothesisGenerator,
    PremiseBuilder,
    ReasoningGraphBuilder,
    UncertaintyEstimator,
)
from duplicate_question_app._reasoning.plugins import get_plugin_registry
from duplicate_question_app._reasoning.premise_builder import DefaultPremiseBuilder
from duplicate_question_app._reasoning.reasoning_graph import DefaultReasoningGraphBuilder
from duplicate_question_app._reasoning.reasoning_result import (
    EvidenceType,
    ProcessingMetadata,
    ReasoningResult,
)
from duplicate_question_app._reasoning.reasoning_trace import TraceRecorder
from duplicate_question_app._reasoning.uncertainty_estimator import DefaultUncertaintyEstimator
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class ReasoningEngine:
    def __init__(
        self,
        premise_builder: PremiseBuilder | None = None,
        hypothesis_generator: HypothesisGenerator | None = None,
        evidence_chain: EvidenceChain | None = None,
        graph_builder: ReasoningGraphBuilder | None = None,
        conflict_resolver: ConflictResolver | None = None,
        uncertainty_estimator: UncertaintyEstimator | None = None,
        confidence_reasoner: ConfidenceReasoner | None = None,
        decision_reasoner: DecisionReasoner | None = None,
    ):
        self._premise_builder = premise_builder or DefaultPremiseBuilder()
        self._hypothesis_generator = hypothesis_generator or DefaultHypothesisGenerator()
        self._evidence_chain = evidence_chain or DefaultEvidenceChain()
        self._graph_builder = graph_builder or DefaultReasoningGraphBuilder()
        self._conflict_resolver = conflict_resolver or DefaultConflictResolver()
        self._uncertainty_estimator = uncertainty_estimator or DefaultUncertaintyEstimator()
        self._confidence_reasoner = confidence_reasoner or DefaultConfidenceReasoner()
        self._decision_reasoner = decision_reasoner or DefaultDecisionReasoner()
        self._plugin_registry = get_plugin_registry()

    def reason(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None = None,
        cross_encoder_score: float | None = None,
    ) -> ReasoningResult:
        start = time.perf_counter()
        stages: dict[str, float] = {}
        tracer = TraceRecorder()

        t0 = time.perf_counter()
        with tracer.step("premise_builder", "extract_premises_a"):
            premises_a = self._premise_builder.extract(rep_a, "question_a")
        stages["premise_extraction_a"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("premise_builder", "extract_premises_b"):
            premises_b = self._premise_builder.extract(rep_b, "question_b")
        stages["premise_extraction_b"] = (time.perf_counter() - t0) * 1000

        all_premises = premises_a + premises_b

        t0 = time.perf_counter()
        with tracer.step("hypothesis_generator", "generate_hypotheses"):
            hypotheses = self._hypothesis_generator.generate(premises_a, premises_b, assessment)
        stages["hypothesis_generation"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("evidence_chain", "build_evidence"):
            evidence = self._evidence_chain.build(hypotheses, premises_a, premises_b, assessment)
        stages["evidence_building"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("plugins", "process_plugins"):
            plugin_evidence = self._plugin_registry.process_all(premises_a, premises_b, hypotheses, evidence)
        stages["plugin_processing"] = (time.perf_counter() - t0) * 1000
        evidence.extend(plugin_evidence)

        t0 = time.perf_counter()
        with tracer.step("conflict_resolver", "resolve_conflicts"):
            conflicts = self._conflict_resolver.resolve(premises_a, premises_b, hypotheses, evidence)
        stages["conflict_resolution"] = (time.perf_counter() - t0) * 1000

        all_evidence = evidence + conflicts

        t0 = time.perf_counter()
        with tracer.step("uncertainty_estimator", "estimate_uncertainty"):
            uncertainty = self._uncertainty_estimator.estimate(all_premises, hypotheses, evidence, conflicts)
        stages["uncertainty_estimation"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("confidence_reasoner", "propagate_confidence"):
            confidence = self._confidence_reasoner.propagate(all_premises, hypotheses, all_evidence)
        stages["confidence_propagation"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("decision_reasoner", "make_decision"):
            decision = self._decision_reasoner.decide(
                hypotheses,
                all_evidence,
                confidence,
                uncertainty,
                cross_encoder_score,
            )
        stages["decision_making"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("decision_reasoner", "build_reason"):
            decision_reason = self._decision_reasoner.build_reason(decision, confidence, uncertainty, all_evidence)  # type: ignore[attr-defined]
        stages["reason_building"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("confidence_reasoner", "build_chain"):
            confidence_chain = self._confidence_reasoner.build_chain(all_premises, hypotheses, all_evidence, confidence)  # type: ignore[attr-defined]
        stages["confidence_chain"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with tracer.step("graph_builder", "build_graph"):
            reasoning_graph = self._graph_builder.build(all_premises, hypotheses, all_evidence)
        stages["graph_building"] = (time.perf_counter() - t0) * 1000

        total_ms = (time.perf_counter() - start) * 1000

        supporting_evidence = [e for e in all_evidence if e.evidence_type == EvidenceType.SUPPORTING]
        contradicting_evidence = [
            e for e in all_evidence if e.evidence_type in (EvidenceType.CONTRADICTING, EvidenceType.NEUTRAL)
        ]

        result = ReasoningResult(
            premises=all_premises,
            hypotheses=hypotheses,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            reasoning_graph=reasoning_graph,
            reasoning_trace=tracer.trace,
            confidence_chain=confidence_chain,
            decision=decision,
            decision_reason=decision_reason,
            confidence=confidence,
            uncertainty=uncertainty,
            processing_metadata=ProcessingMetadata(
                total_premises=len(all_premises),
                total_hypotheses=len(hypotheses),
                total_evidence=len(supporting_evidence),
                total_conflicts=len(contradicting_evidence),
                graph_nodes=len(reasoning_graph.nodes),
                graph_edges=len(reasoning_graph.edges),
                processing_time_ms=total_ms,
                stages=stages,
                components_used=[
                    "premise_builder",
                    "hypothesis_generator",
                    "evidence_chain",
                    "graph_builder",
                    "conflict_resolver",
                    "uncertainty_estimator",
                    "confidence_reasoner",
                    "decision_reasoner",
                    "plugins",
                ],
            ),
        )

        return result
