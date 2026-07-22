"""RepresentationBuilder — the top-level orchestrator for Phase 1.4.

Consumes a LinguisticProfile and produces a complete SemanticRepresentation.
"""

from __future__ import annotations

import time

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic import representation as _rep
from duplicate_question_app._semantic.ambiguity_detector import AmbiguityDetector, DefaultAmbiguityDetector
from duplicate_question_app._semantic.concept_extractor import ConceptExtractor, DefaultConceptExtractor
from duplicate_question_app._semantic.confidence import DefaultSemanticConfidence, SemanticConfidence
from duplicate_question_app._semantic.context_builder import ContextBuilder, DefaultContextBuilder
from duplicate_question_app._semantic.relation_extractor import DefaultRelationExtractor, RelationExtractor
from duplicate_question_app._semantic.semantic_graph import SemanticGraph
from duplicate_question_app._semantic.semantic_roles import DefaultSemanticRoleAnalyzer, SemanticRoleAnalyzer

log = get_logger(__name__)


class RepresentationBuilder:
    def __init__(
        self,
        concept_extractor: ConceptExtractor | None = None,
        relation_extractor: RelationExtractor | None = None,
        role_analyzer: SemanticRoleAnalyzer | None = None,
        context_builder: ContextBuilder | None = None,
        ambiguity_detector: AmbiguityDetector | None = None,
        confidence: SemanticConfidence | None = None,
    ) -> None:
        self._concept_extractor = concept_extractor or DefaultConceptExtractor()
        self._relation_extractor = relation_extractor or DefaultRelationExtractor()
        self._role_analyzer = role_analyzer or DefaultSemanticRoleAnalyzer()
        self._context_builder = context_builder or DefaultContextBuilder()
        self._ambiguity_detector = ambiguity_detector or DefaultAmbiguityDetector()
        self._confidence = confidence or DefaultSemanticConfidence()

    def build(self, profile: LinguisticProfile) -> _rep.SemanticRepresentation:
        t0 = time.perf_counter()
        stages: dict[str, float] = {}
        representation = _rep.SemanticRepresentation()

        t_start = time.perf_counter()
        concepts = self._concept_extractor.extract(profile)
        stages["concept_extraction"] = (time.perf_counter() - t_start) * 1000
        representation.concepts = [
            _rep.SemanticConcept(
                id=c.id,
                label=c.label,
                normalized_form=c.label,
                original_forms=[c.label],
                confidence=c.confidence,
                source=c.node_type,
                metadata=c.metadata,
            )
            for c in concepts
        ]

        t_start = time.perf_counter()
        graph = SemanticGraph()
        for c in concepts:
            graph.add_node(c)
        relations = self._relation_extractor.extract(profile, concepts)
        for r in relations:
            graph.add_edge(r)
        stages["relation_extraction"] = (time.perf_counter() - t_start) * 1000
        representation.semantic_graph = graph
        representation.relationships = [
            _rep.SemanticRelation(
                source_id=r.source_id,
                target_id=r.target_id,
                relation_type=r.relation_type,
                confidence=r.confidence,
                metadata=r.metadata,
            )
            for r in relations
        ]

        t_start = time.perf_counter()
        roles = self._role_analyzer.analyze(profile, concepts)
        representation.semantic_roles = self._role_analyzer.to_assignments(roles)  # type: ignore[attr-defined]
        stages["role_analysis"] = (time.perf_counter() - t_start) * 1000

        representation.intent_summary = profile.intent
        representation.domain = profile.domain or "general"
        representation.entities = profile.entities
        representation.actions = [c.label for c in concepts if c.node_type == "action"]
        representation.objects = [c.label for c in concepts if c.node_type == "concept"]
        representation.attributes = []

        t_start = time.perf_counter()
        representation.context = self._context_builder.build(profile, representation)
        stages["context_building"] = (time.perf_counter() - t_start) * 1000

        t_start = time.perf_counter()
        representation.ambiguities = self._ambiguity_detector.detect(profile, representation)
        stages["ambiguity_detection"] = (time.perf_counter() - t_start) * 1000

        t_start = time.perf_counter()
        confidence_detail = self._confidence.compute(profile, representation)
        stages["confidence_computation"] = (time.perf_counter() - t_start) * 1000
        representation.confidence_detail = confidence_detail
        representation.semantic_confidence = confidence_detail.get("overall", 0.0)

        total_ms = (time.perf_counter() - t0) * 1000
        representation.processing_metadata = _rep.ProcessingMetadata(
            total_concepts=len(concepts),
            total_relations=len(relations),
            total_roles=len(representation.semantic_roles),
            ambiguity_count=len(representation.ambiguities),
            processing_time_ms=total_ms,
            stages=stages,
        )

        log.info(
            "Built SemanticRepresentation in %.1fms (%d concepts, %d relations, %d ambiguities)",
            total_ms,
            len(concepts),
            len(relations),
            len(representation.ambiguities),
        )
        return representation
