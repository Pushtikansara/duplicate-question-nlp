"""Semantic Knowledge Representation — Phase 1.4.

Transforms a LinguisticProfile into a structured SemanticRepresentation
embedding concepts, relations, roles, context, and ambiguity detection.
"""

from duplicate_question_app._semantic.ambiguity_detector import AmbiguityDetector, DefaultAmbiguityDetector
from duplicate_question_app._semantic.concept_extractor import ConceptExtractor, DefaultConceptExtractor
from duplicate_question_app._semantic.confidence import DefaultSemanticConfidence, SemanticConfidence
from duplicate_question_app._semantic.context_builder import ContextBuilder, DefaultContextBuilder
from duplicate_question_app._semantic.relation_extractor import DefaultRelationExtractor, RelationExtractor
from duplicate_question_app._semantic.representation import (
    AmbiguityEntry,
    ProcessingMetadata,
    SemanticConcept,
    SemanticRelation,
    SemanticRepresentation,
    SemanticRoleAssignment,
)
from duplicate_question_app._semantic.representation_builder import RepresentationBuilder
from duplicate_question_app._semantic.semantic_graph import SemanticGraph, SemanticNode
from duplicate_question_app._semantic.semantic_roles import DefaultSemanticRoleAnalyzer, SemanticRoleAnalyzer

__all__ = [
    "AmbiguityDetector",
    "DefaultAmbiguityDetector",
    "ConceptExtractor",
    "DefaultConceptExtractor",
    "SemanticConfidence",
    "DefaultSemanticConfidence",
    "ContextBuilder",
    "DefaultContextBuilder",
    "RelationExtractor",
    "DefaultRelationExtractor",
    "SemanticRepresentation",
    "SemanticConcept",
    "SemanticRelation",
    "SemanticRoleAssignment",
    "AmbiguityEntry",
    "ProcessingMetadata",
    "SemanticGraph",
    "SemanticNode",
    "SemanticRoleAnalyzer",
    "DefaultSemanticRoleAnalyzer",
    "RepresentationBuilder",
]
