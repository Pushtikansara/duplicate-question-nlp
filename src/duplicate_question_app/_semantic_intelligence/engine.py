"""SemanticIntelligenceEngine — the main orchestrator of the Semantic Intelligence Layer.

Consumes two SemanticRepresentation objects and produces a SemanticAssessment.
Coordinates all sub-components: matchers, detectors, evidence builder, fusion, decision.
"""

from __future__ import annotations

import time

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.concept_matcher import DefaultConceptMatcher
from duplicate_question_app._semantic_intelligence.confidence_fusion import DefaultConfidenceFusion
from duplicate_question_app._semantic_intelligence.conflict_detector import DefaultConflictDetector
from duplicate_question_app._semantic_intelligence.context_matcher import DefaultContextMatcher
from duplicate_question_app._semantic_intelligence.decision_support import DefaultDecisionSupport
from duplicate_question_app._semantic_intelligence.entity_matcher import DefaultEntityMatcher
from duplicate_question_app._semantic_intelligence.evidence_builder import DefaultEvidenceBuilder
from duplicate_question_app._semantic_intelligence.intent_matcher import DefaultIntentMatcher
from duplicate_question_app._semantic_intelligence.relation_matcher import DefaultRelationMatcher
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    ContextSimilarity,
    EntityOverlap,
    EvidenceItem,
    IntentSimilarity,
    ProcessingMetadata,
    RelationSimilarity,
    SemanticAssessment,
)
from duplicate_question_app._semantic_intelligence.semantic_similarity import DefaultSemanticSimilarity


class SemanticIntelligenceEngine:
    def __init__(
        self,
        concept_matcher=None,
        entity_matcher=None,
        relation_matcher=None,
        intent_matcher=None,
        context_matcher=None,
        conflict_detector=None,
        evidence_builder=None,
        confidence_fusion=None,
        semantic_similarity=None,
        decision_support=None,
    ):
        self._concept_matcher = concept_matcher or DefaultConceptMatcher()
        self._entity_matcher = entity_matcher or DefaultEntityMatcher()
        self._relation_matcher = relation_matcher or DefaultRelationMatcher()
        self._intent_matcher = intent_matcher or DefaultIntentMatcher()
        self._context_matcher = context_matcher or DefaultContextMatcher()
        self._conflict_detector = conflict_detector or DefaultConflictDetector()
        self._evidence_builder = evidence_builder or DefaultEvidenceBuilder()
        self._confidence_fusion = confidence_fusion or DefaultConfidenceFusion()
        self._semantic_similarity = semantic_similarity or DefaultSemanticSimilarity()
        self._decision_support = decision_support or DefaultDecisionSupport()

    def assess(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> SemanticAssessment:
        start = time.perf_counter()
        stages = {}

        t0 = time.perf_counter()
        concept_result = self._concept_matcher.match(rep_a, rep_b)
        stages["concept_matching"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        entity_result = self._entity_matcher.match(rep_a, rep_b)
        stages["entity_matching"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        relation_result = self._relation_matcher.match(rep_a, rep_b)
        stages["relation_matching"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        intent_result = self._intent_matcher.match(rep_a, rep_b)
        stages["intent_matching"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        context_result = self._context_matcher.match(rep_a, rep_b)
        stages["context_matching"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        raw_conflicts = self._conflict_detector.detect(rep_a, rep_b)
        stages["conflict_detection"] = (time.perf_counter() - t0) * 1000

        scores = {
            "concept_similarity": concept_result["overlap_score"],
            "entity_similarity": entity_result["overlap_score"],
            "relation_similarity": relation_result["score"],
            "intent_similarity": intent_result["score"],
            "context_similarity": context_result["score"],
        }

        t0 = time.perf_counter()
        fusion_result = self._confidence_fusion.compute(scores)
        stages["confidence_fusion"] = (time.perf_counter() - t0) * 1000

        overall_sim = fusion_result["overall"]

        t0 = time.perf_counter()
        conflicts = [
            Conflict(
                conflict_type=c["conflict_type"],
                description=c["description"],
                severity=c["severity"],
                source=c["source"],
                detail=c.get("detail", {}),
            )
            for c in raw_conflicts
        ]
        stages["conflict_construction"] = (time.perf_counter() - t0) * 1000

        assessment = SemanticAssessment(
            semantic_similarity=overall_sim,
            concept_overlap=ConceptOverlap(
                overlap_score=concept_result["overlap_score"],
                shared_concepts=concept_result["shared_concepts"],
                missing_in_a=concept_result["missing_in_a"],
                missing_in_b=concept_result["missing_in_b"],
                total_a=concept_result["total_a"],
                total_b=concept_result["total_b"],
                detail=concept_result.get("detail", {}),
            ),
            entity_overlap=EntityOverlap(
                overlap_score=entity_result["overlap_score"],
                shared_entities=entity_result["shared_entities"],
                missing_in_a=entity_result["missing_in_a"],
                missing_in_b=entity_result["missing_in_b"],
                conflicts=entity_result["conflicts"],
                total_a=entity_result["total_a"],
                total_b=entity_result["total_b"],
                detail=entity_result.get("detail", {}),
            ),
            intent_similarity=IntentSimilarity(
                score=intent_result["score"],
                confidence=intent_result["confidence"],
                reason=intent_result["reason"],
                detail=intent_result.get("detail", {}),
            ),
            relation_similarity=RelationSimilarity(
                score=relation_result["score"],
                matching_relations=relation_result["matching_relations"],
                missing_in_a=relation_result["missing_in_a"],
                missing_in_b=relation_result["missing_in_b"],
                total_a=relation_result["total_a"],
                total_b=relation_result["total_b"],
                detail=relation_result.get("detail", {}),
            ),
            context_similarity=ContextSimilarity(
                score=context_result["score"],
                domain_match=context_result["domain_match"],
                domain_a=context_result["domain_a"],
                domain_b=context_result["domain_b"],
                shared_context_keys=context_result["shared_context_keys"],
                constraints_match=context_result["constraints_match"],
                detail=context_result.get("detail", {}),
            ),
            conflicts=conflicts,
            confidence=fusion_result["overall"],
            confidence_detail={
                "raw_scores": fusion_result.get("raw_scores", {}),
                "weighted_scores": fusion_result.get("weighted_scores", {}),
                "weights": fusion_result.get("weights", {}),
            },
        )

        t0 = time.perf_counter()
        raw_evidence = self._evidence_builder.build(assessment)
        stages["evidence_building"] = (time.perf_counter() - t0) * 1000

        assessment.supporting_evidence = [
            EvidenceItem(
                category=e["category"],
                status=e["status"],
                message=e["message"],
                confidence=e["confidence"],
            )
            for e in raw_evidence
        ]

        t0 = time.perf_counter()
        decision = self._decision_support.evaluate(assessment)
        stages["decision_support"] = (time.perf_counter() - t0) * 1000

        assessment.recommendation = decision["recommendation"]
        assessment.recommendation_reason = decision["reason"]

        total_ms = (time.perf_counter() - start) * 1000
        assessment.processing_metadata = ProcessingMetadata(
            processing_time_ms=total_ms,
            stages=stages,
            components_used=[
                "concept_matcher",
                "entity_matcher",
                "relation_matcher",
                "intent_matcher",
                "context_matcher",
                "conflict_detector",
                "evidence_builder",
                "confidence_fusion",
                "semantic_similarity",
                "decision_support",
            ],
        )

        return assessment
