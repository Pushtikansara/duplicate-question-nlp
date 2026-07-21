"""Linguistic Intelligence Layer — transforms shallow features into a rich LinguisticProfile.

Raw Text → Perception Engine → Linguistic Intelligence → LinguisticProfile → CognitiveRepresentation
"""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.complexity_analyzer import (
    ComplexityAnalyzer,
    DefaultComplexityAnalyzer,
)
from duplicate_question_app._linguistic_intelligence.confidence_estimator import (
    ConfidenceEstimator,
    DefaultConfidenceEstimator,
)
from duplicate_question_app._linguistic_intelligence.domain_detector import DefaultDomainDetector, DomainDetector
from duplicate_question_app._linguistic_intelligence.keyword_extractor import DefaultKeywordExtractor, KeywordExtractor
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._linguistic_intelligence.profile_builder import LinguisticProfileBuilder
from duplicate_question_app._linguistic_intelligence.quality_metrics import DefaultQualityMetrics, QualityMetrics
from duplicate_question_app._linguistic_intelligence.question_classifier import (
    DefaultQuestionClassifier,
    QuestionClassifier,
)

__all__ = [
    "ComplexityAnalyzer",
    "ConfidenceEstimator",
    "DefaultComplexityAnalyzer",
    "DefaultConfidenceEstimator",
    "DefaultDomainDetector",
    "DefaultKeywordExtractor",
    "DefaultQualityMetrics",
    "DefaultQuestionClassifier",
    "DomainDetector",
    "KeywordExtractor",
    "LinguisticProfile",
    "LinguisticProfileBuilder",
    "ProfileBuilderResult",
    "QualityMetrics",
    "QuestionClassifier",
]
