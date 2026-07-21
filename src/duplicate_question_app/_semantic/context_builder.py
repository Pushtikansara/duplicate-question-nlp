"""ContextBuilder — enriches the semantic representation with contextual metadata.

Uses existing profile information to build a context dictionary
without calling external services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile
from duplicate_question_app._semantic.representation import SemanticRepresentation

log = get_logger(__name__)


class ContextBuilder(ABC):
    @abstractmethod
    def build(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict: ...


class DefaultContextBuilder(ContextBuilder):
    def __init__(self) -> None:
        self._logger = log

    def build(self, profile: LinguisticProfile, representation: SemanticRepresentation) -> dict:
        context = {
            "language": profile.language,
            "language_confidence": profile.language_confidence,
            "is_question": profile.question_type is not None and profile.question_type != "declarative",
            "question_type": profile.question_type,
            "has_negation": profile.negation,
            "negation_count": profile.negation_count,
            "has_contradiction": profile.contradiction,
            "contradiction_score": profile.contradiction_score,
            "complexity": profile.complexity.overall,
            "readability": profile.readability.flesch_reading_ease,
            "lexical_density": profile.lexical_features.lexical_density,
            "word_count": profile.token_statistics.total,
            "sentence_count": profile.sentence_statistics.total,
            "entity_count": profile.entity_count,
            "keyword_count": len(profile.keywords),
            "linguistic_quality": profile.quality_metrics.quality_score,
            "analysis_confidence": profile.analysis_confidence.overall,
        }
        if profile.negation:
            context["negation_present"] = True
        if profile.contradiction:
            context["contradiction_present"] = True
        self._logger.debug("Built context with %d keys", len(context))
        return context
