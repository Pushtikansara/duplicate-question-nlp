"""ConfidenceEstimator — estimates overall and per-analyzer confidence.

Aggregates confidence scores from all analyzers into a unified
AnalysisConfidence object with holistic calibration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, LinguisticProfile

log = get_logger(__name__)


class ConfidenceEstimator(ABC):
    @abstractmethod
    def estimate(self, profile: LinguisticProfile) -> AnalysisConfidence: ...


class DefaultConfidenceEstimator(ConfidenceEstimator):
    def __init__(self) -> None:
        self._logger = get_logger(f"{__name__}.DefaultConfidenceEstimator")

    def estimate(self, profile: LinguisticProfile) -> AnalysisConfidence:
        lang_conf = profile.language_confidence
        intent_conf = profile.intent_confidence if profile.intent else 0.0
        entity_count = profile.entity_count
        entity_conf = min(1.0, entity_count * 0.1) if entity_count > 0 else 0.0
        kw_count = len(profile.keywords)
        kw_conf = min(1.0, kw_count * 0.05) if kw_count > 0 else 0.0
        qt_conf = 0.0
        if profile.question_type and profile.question_type != "declarative":
            qt_conf = 0.7
        elif profile.question_type:
            qt_conf = 0.3
        complexity_conf = 0.7 if profile.complexity.overall > 0 else 0.0
        domain_conf = profile.domain_confidence if profile.domain else 0.0
        per_analyzer = {
            "language": lang_conf,
            "intent": intent_conf,
            "entities": entity_conf,
            "keywords": kw_conf,
            "question_type": qt_conf,
            "complexity": complexity_conf,
            "domain": domain_conf,
        }
        present = [v for v in per_analyzer.values() if v > 0]
        overall = sum(present) / len(present) if present else 0.0
        return AnalysisConfidence(
            overall=overall,
            language=lang_conf,
            intent=intent_conf,
            entities=entity_conf,
            keyword=kw_conf,
            question_type=qt_conf,
            complexity=complexity_conf,
            domain=domain_conf,
            per_analyzer=per_analyzer,
        )
