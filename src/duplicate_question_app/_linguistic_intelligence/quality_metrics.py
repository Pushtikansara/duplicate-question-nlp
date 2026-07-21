"""QualityMetrics — evaluates quality of the linguistic analysis.

Produces metrics:
  - coverage: percentage of analyzers that produced non-null results
  - completeness: how many profile fields were populated
  - confidence: weighted average of per-analyzer confidence
  - latency: total processing time
  - quality_score: holistic quality score
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._linguistic_intelligence.profile import LinguisticProfile, QualityMetricsData

log = get_logger(__name__)

_REQUIRED_FIELDS: set[str] = {
    "language",
    "intent",
    "question_type",
    "domain",
}


class QualityMetrics(ABC):
    @abstractmethod
    def evaluate(self, profile: LinguisticProfile, latency_ms: float = 0.0) -> QualityMetricsData: ...


class DefaultQualityMetrics(QualityMetrics):
    def __init__(self) -> None:
        self._logger = get_logger(f"{__name__}.DefaultQualityMetrics")

    def evaluate(self, profile: LinguisticProfile, latency_ms: float = 0.0) -> QualityMetricsData:
        covered = 0
        total_analyzers = 7
        if profile.language:
            covered += 1
        if profile.intent:
            covered += 1
        if profile.question_type:
            covered += 1
        if profile.domain:
            covered += 1
        if profile.entity_count > 0:
            covered += 1
        if profile.keywords:
            covered += 1
        if profile.complexity.overall > 0:
            covered += 1

        coverage = covered / total_analyzers if total_analyzers > 0 else 0.0
        completeness = self._compute_completeness(profile)
        confidence = profile.analysis_confidence.overall if profile.analysis_confidence.overall > 0 else 0.5
        quality = coverage * 0.3 + completeness * 0.3 + confidence * 0.4

        return QualityMetricsData(
            coverage=coverage,
            completeness=completeness,
            confidence=confidence,
            latency_ms=latency_ms,
            processing_time_ms=latency_ms,
            warnings=list(profile.quality_metrics.warnings),
            errors=list(profile.quality_metrics.errors),
            quality_score=quality,
            per_metric={
                "coverage": coverage,
                "completeness": completeness,
                "confidence": confidence,
                "quality": quality,
            },
        )

    @staticmethod
    def _compute_completeness(profile: LinguisticProfile) -> float:
        filled = 0
        if profile.language:
            filled += 1
        if profile.intent:
            filled += 1
        if profile.question_type:
            filled += 1
        if profile.domain:
            filled += 1
        if profile.entity_count > 0:
            filled += 1
        if len(profile.keywords) >= 3:
            filled += 1
        if profile.complexity.overall > 0:
            filled += 1
        if profile.readability.flesch_reading_ease > 0:
            filled += 1
        if profile.negation_count > 0 or profile.negation:
            filled += 1
        if profile.lexical_features.lexical_density > 0:
            filled += 1
        total_fields = 10
        return filled / total_fields if total_fields > 0 else 0.0
