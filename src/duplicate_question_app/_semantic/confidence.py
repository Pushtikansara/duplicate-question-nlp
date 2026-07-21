"""SemanticConfidence — computes holistic and per-component confidence for the semantic representation.

Uses:
  - concept coverage: ratio of potential concepts actually extracted
  - entity confidence: average entity confidence from profile
  - relation completeness: ratio of concepts with at least one relation
  - linguistic confidence: overall linguistic analysis confidence
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.representation import SemanticRepresentation

log = get_logger(__name__)


class SemanticConfidence(ABC):
    @abstractmethod
    def compute(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict: ...


class DefaultSemanticConfidence(SemanticConfidence):
    def __init__(self) -> None:
        self._logger = log

    def compute(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict:
        concept_count = len(representation.concepts)
        entity_count = profile.entity_count
        keyword_count = len(profile.keywords)
        potential = max(entity_count + keyword_count, 1)

        concept_coverage = concept_count / potential if potential > 0 else 0.0
        concept_coverage = min(1.0, concept_coverage)

        avg_entity_conf = 0.0
        if profile.entities:
            avg_entity_conf = sum(e.get("confidence", 0.0) for e in profile.entities) / len(profile.entities)

        if representation.semantic_graph is not None:
            graph = representation.semantic_graph
            connected = len({e.source_id for e in graph.edges} | {e.target_id for e in graph.edges})
            total_concepts = max(graph.node_count(), 1)
            relation_completeness = connected / total_concepts if total_concepts > 0 else 0.0
        else:
            relation_completeness = 0.0

        linguistic_conf = profile.analysis_confidence.overall if profile.analysis_confidence.overall > 0 else 0.5
        intent_conf = profile.intent_confidence if profile.intent else 0.0
        domain_conf = profile.domain_confidence if profile.domain else 0.0

        confidence = (
            concept_coverage * 0.25
            + avg_entity_conf * 0.15
            + relation_completeness * 0.20
            + linguistic_conf * 0.20
            + intent_conf * 0.10
            + domain_conf * 0.10
        )

        detail = {
            "concept_coverage": concept_coverage,
            "avg_entity_confidence": avg_entity_conf,
            "relation_completeness": relation_completeness,
            "linguistic_confidence": linguistic_conf,
            "intent_confidence": intent_conf,
            "domain_confidence": domain_conf,
            "overall": confidence,
        }

        self._logger.debug(
            "Semantic confidence: %.3f (coverage=%.2f, relations=%.2f, linguistic=%.2f)",
            confidence,
            concept_coverage,
            relation_completeness,
            linguistic_conf,
        )
        return detail
