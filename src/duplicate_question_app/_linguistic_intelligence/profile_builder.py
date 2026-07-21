"""LinguisticProfileBuilder — orchestrates all analyzers into a unified LinguisticProfile.

This is the central orchestrator of the Linguistic Intelligence Layer.
Every analyzer is injected via constructor (Dependency Injection).
The builder produces a single LinguisticProfile embedded in CognitiveRepresentation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from duplicate_question_app._config.logging_setup import get_logger
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
from duplicate_question_app._linguistic_intelligence.profile import (
    LinguisticProfile,
)
from duplicate_question_app._linguistic_intelligence.quality_metrics import DefaultQualityMetrics, QualityMetrics
from duplicate_question_app._linguistic_intelligence.question_classifier import (
    DefaultQuestionClassifier,
    QuestionClassifier,
)
from duplicate_question_app._perception.adapters import (
    EntityAdapter,
    IntentAdapter,
    LexicalAdapter,
    NegationAdapter,
)
from duplicate_question_app._perception.cognitive_representation import CognitiveRepresentation

log = get_logger(__name__)


@dataclass
class ProfileBuilderResult:
    profile: LinguisticProfile
    success: bool
    timing_ms: float
    error: str | None = None
    stage_timing: dict[str, float] = field(default_factory=dict)


class LinguisticProfileBuilder:
    def __init__(
        self,
        entity_adapter: EntityAdapter | None = None,
        negation_adapter: NegationAdapter | None = None,
        intent_adapter: IntentAdapter | None = None,
        lexical_adapter: LexicalAdapter | None = None,
        question_classifier: QuestionClassifier | None = None,
        complexity_analyzer: ComplexityAnalyzer | None = None,
        keyword_extractor: KeywordExtractor | None = None,
        domain_detector: DomainDetector | None = None,
        confidence_estimator: ConfidenceEstimator | None = None,
        quality_metrics: QualityMetrics | None = None,
    ):
        from duplicate_question_app._linguistic_intelligence.adapters.perception_adapters import (
            get_entity_adapter as _gea,
        )
        from duplicate_question_app._linguistic_intelligence.adapters.perception_adapters import (
            get_intent_adapter as _gia,
        )
        from duplicate_question_app._linguistic_intelligence.adapters.perception_adapters import (
            get_lexical_adapter as _gla,
        )
        from duplicate_question_app._linguistic_intelligence.adapters.perception_adapters import (
            get_negation_adapter as _gna,
        )

        self._entity = entity_adapter or _gea()
        self._negation = negation_adapter or _gna()
        self._intent = intent_adapter or _gia()
        self._lexical = lexical_adapter or _gla()
        self._question = question_classifier or DefaultQuestionClassifier()
        self._complexity = complexity_analyzer or DefaultComplexityAnalyzer()
        self._keywords = keyword_extractor or DefaultKeywordExtractor()
        self._domain = domain_detector or DefaultDomainDetector()
        self._confidence = confidence_estimator or DefaultConfidenceEstimator()
        self._quality = quality_metrics or DefaultQualityMetrics()
        self._logger = log

    def build(self, representation: CognitiveRepresentation) -> ProfileBuilderResult:
        start = time.perf_counter()
        stage_timing: dict[str, float] = {}
        profile = LinguisticProfile()

        if not representation or not representation.normalized_text:
            elapsed = (time.perf_counter() - start) * 1000
            return ProfileBuilderResult(
                profile=profile, success=False, timing_ms=elapsed, error="No normalized text available"
            )

        text = representation.normalized_text

        try:
            t0 = time.perf_counter()
            profile.language = representation.language
            profile.language_confidence = representation.language_confidence
            stage_timing["language"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            intent_type, intent_conf = self._intent.detect(text)
            profile.intent = intent_type
            profile.intent_confidence = intent_conf
            stage_timing["intent"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            entities = self._entity.extract(text)
            profile.entities = [{"type": e.entity_type, "value": e.value, "confidence": e.confidence} for e in entities]
            profile.entity_count = len(entities)
            stage_timing["entities"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            negations = self._negation.detect(text)
            profile.negation = len(negations) > 0
            profile.negation_count = len(negations)
            stage_timing["negation"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            keywords, kw_scores, lexical = self._keywords.extract(text)
            profile.keywords = keywords
            profile.keyword_scores = kw_scores
            profile.lexical_features = lexical
            stage_timing["keywords"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            qt, qc, qt_conf = self._question.classify(text)
            profile.question_type = qt
            profile.question_class = qc
            stage_timing["question_classify"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            tok_stats, sent_stats, complexity, readability = self._complexity.analyze(text)
            profile.token_statistics = tok_stats
            profile.sentence_statistics = sent_stats
            profile.complexity = complexity
            profile.readability = readability
            stage_timing["complexity"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            domain, domain_conf = self._domain.detect(text)
            profile.domain = domain
            profile.domain_confidence = domain_conf
            stage_timing["domain"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            analysis_conf = self._confidence.estimate(profile)
            profile.analysis_confidence = analysis_conf
            stage_timing["confidence"] = (time.perf_counter() - t0) * 1000

            elapsed = (time.perf_counter() - start) * 1000
            t0 = time.perf_counter()
            qm = self._quality.evaluate(profile, latency_ms=elapsed)
            profile.quality_metrics = qm
            stage_timing["quality"] = (time.perf_counter() - t0) * 1000

            total_elapsed = (time.perf_counter() - start) * 1000
            return ProfileBuilderResult(
                profile=profile, success=True, timing_ms=total_elapsed, stage_timing=stage_timing
            )

        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            self._logger.error("ProfileBuilder failed after %.2fms: %s", elapsed, exc)
            profile.quality_metrics.errors.append(str(exc))
            return ProfileBuilderResult(
                profile=profile, success=False, timing_ms=elapsed, error=str(exc), stage_timing=stage_timing
            )
