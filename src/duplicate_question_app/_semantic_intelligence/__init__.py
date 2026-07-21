"""Semantic Intelligence Engine — Phase 2.0.

Compares two SemanticRepresentation objects and produces a SemanticAssessment
with similarity scores, conflicts, evidence, confidence, and recommendations.
"""

from duplicate_question_app._semantic_intelligence.concept_matcher import ConceptMatcher, DefaultConceptMatcher
from duplicate_question_app._semantic_intelligence.confidence_fusion import ConfidenceFusion, DefaultConfidenceFusion
from duplicate_question_app._semantic_intelligence.conflict_detector import ConflictDetector, DefaultConflictDetector
from duplicate_question_app._semantic_intelligence.context_matcher import ContextMatcher, DefaultContextMatcher
from duplicate_question_app._semantic_intelligence.decision_support import DecisionSupport, DefaultDecisionSupport
from duplicate_question_app._semantic_intelligence.engine import SemanticIntelligenceEngine
from duplicate_question_app._semantic_intelligence.entity_matcher import DefaultEntityMatcher, EntityMatcher
from duplicate_question_app._semantic_intelligence.evidence_builder import DefaultEvidenceBuilder, EvidenceBuilder
from duplicate_question_app._semantic_intelligence.fusion import DecisionFusion, FusionStrategy
from duplicate_question_app._semantic_intelligence.intent_matcher import DefaultIntentMatcher, IntentMatcher
from duplicate_question_app._semantic_intelligence.interfaces import ConceptMatcher as ConceptMatcherABC
from duplicate_question_app._semantic_intelligence.interfaces import ConfidenceFusion as ConfidenceFusionABC
from duplicate_question_app._semantic_intelligence.interfaces import ConflictDetector as ConflictDetectorABC
from duplicate_question_app._semantic_intelligence.interfaces import ContextMatcher as ContextMatcherABC
from duplicate_question_app._semantic_intelligence.interfaces import DecisionSupport as DecisionSupportABC
from duplicate_question_app._semantic_intelligence.interfaces import EntityMatcher as EntityMatcherABC
from duplicate_question_app._semantic_intelligence.interfaces import EvidenceBuilder as EvidenceBuilderABC
from duplicate_question_app._semantic_intelligence.interfaces import IntentMatcher as IntentMatcherABC
from duplicate_question_app._semantic_intelligence.interfaces import RelationMatcher as RelationMatcherABC
from duplicate_question_app._semantic_intelligence.interfaces import (
    SemanticIntelligenceEngine as SemanticIntelligenceEngineABC,
)
from duplicate_question_app._semantic_intelligence.interfaces import SemanticSimilarity as SemanticSimilarityABC
from duplicate_question_app._semantic_intelligence.relation_matcher import DefaultRelationMatcher, RelationMatcher
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    ContextSimilarity,
    EntityOverlap,
    EvidenceItem,
    IntentSimilarity,
    Recommendation,
    RelationSimilarity,
    SemanticAssessment,
)
from duplicate_question_app._semantic_intelligence.semantic_pipeline import SemanticPipelineService
from duplicate_question_app._semantic_intelligence.semantic_similarity import (
    DefaultSemanticSimilarity,
    SemanticSimilarity,
)

__all__ = [
    "SemanticIntelligenceEngine",
    "SemanticAssessment",
    "ConceptOverlap",
    "EntityOverlap",
    "IntentSimilarity",
    "RelationSimilarity",
    "ContextSimilarity",
    "Conflict",
    "EvidenceItem",
    "Recommendation",
    "ConceptMatcher",
    "DefaultConceptMatcher",
    "EntityMatcher",
    "DefaultEntityMatcher",
    "RelationMatcher",
    "DefaultRelationMatcher",
    "IntentMatcher",
    "DefaultIntentMatcher",
    "ContextMatcher",
    "DefaultContextMatcher",
    "ConflictDetector",
    "DefaultConflictDetector",
    "EvidenceBuilder",
    "DefaultEvidenceBuilder",
    "ConfidenceFusion",
    "DefaultConfidenceFusion",
    "SemanticSimilarity",
    "DefaultSemanticSimilarity",
    "DecisionSupport",
    "DefaultDecisionSupport",
    "ConceptMatcherABC",
    "EntityMatcherABC",
    "RelationMatcherABC",
    "IntentMatcherABC",
    "ContextMatcherABC",
    "ConflictDetectorABC",
    "EvidenceBuilderABC",
    "ConfidenceFusionABC",
    "SemanticSimilarityABC",
    "DecisionSupportABC",
    "SemanticIntelligenceEngineABC",
    "DecisionFusion",
    "FusionStrategy",
    "SemanticPipelineService",
]
