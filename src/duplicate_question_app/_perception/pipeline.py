from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._inference.cache import (
    cached_linguistic_profile,
    cached_perception,
    cached_semantic_representation,
)
from duplicate_question_app._perception.cognitive_representation import CognitiveRepresentation, ValidationReport
from duplicate_question_app._perception.config import PerceptionPipelineConfig
from duplicate_question_app._perception.language_detector import HeuristicLanguageDetector, LanguageDetector
from duplicate_question_app._perception.linguistic_orchestrator import (
    DefaultLinguisticOrchestrator,
    LinguisticOrchestrator,
)
from duplicate_question_app._perception.metadata_extractor import DefaultMetadataExtractor, MetadataExtractor
from duplicate_question_app._perception.normalizer import DefaultTextNormalizer, TextNormalizer
from duplicate_question_app._perception.plugin_loader import DefaultPluginLoader, PluginLoader
from duplicate_question_app._perception.structural_analyzer import DefaultStructuralAnalyzer, StructuralAnalyzer
from duplicate_question_app._perception.tokenizer_wrapper import Tokenizer, TokenizerFactory
from duplicate_question_app._perception.validator import DefaultValidator, TextValidator
from duplicate_question_app._profiling import profile

if TYPE_CHECKING:
    from duplicate_question_app._linguistic_intelligence.profile_builder import LinguisticProfileBuilder

log = get_logger(__name__)


@dataclass
class PipelineResult:
    representation: CognitiveRepresentation | None = None
    success: bool = False
    error: str | None = None
    timing_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)


class PerceptionPipeline:
    def __init__(
        self,
        config: PerceptionPipelineConfig | None = None,
        normalizer: TextNormalizer | None = None,
        language_detector: LanguageDetector | None = None,
        tokenizer: Tokenizer | None = None,
        structural_analyzer: StructuralAnalyzer | None = None,
        linguistic_orchestrator: LinguisticOrchestrator | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        validator: TextValidator | None = None,
        plugin_loader: PluginLoader | None = None,
        profile_builder: LinguisticProfileBuilder | None = None,
        representation_builder: Any | None = None,
    ):
        cfg = config or PerceptionPipelineConfig()
        self._normalizer = normalizer or DefaultTextNormalizer(cfg.normalizer)
        self._language_detector = language_detector or HeuristicLanguageDetector(cfg.language_detector)
        self._tokenizer = tokenizer or TokenizerFactory.create(cfg.tokenizer)
        self._structural_analyzer = structural_analyzer or DefaultStructuralAnalyzer(cfg.structural_analyzer)
        self._linguistic_orchestrator = linguistic_orchestrator or DefaultLinguisticOrchestrator(
            cfg.linguistic_orchestrator
        )
        self._metadata_extractor = metadata_extractor or DefaultMetadataExtractor(cfg.metadata_extractor)
        self._validator = validator or DefaultValidator(cfg.validator)
        self._plugin_loader = plugin_loader or DefaultPluginLoader(cfg.plugin_loader)
        if profile_builder is not None:
            self._profile_builder = profile_builder
        else:
            from duplicate_question_app._linguistic_intelligence.profile_builder import LinguisticProfileBuilder

            self._profile_builder = LinguisticProfileBuilder()
        self._representation_builder = representation_builder
        self._config = cfg
        self._logger = log

    @profile("perception_pipeline")
    def run(self, text: str, **kwargs: Any) -> PipelineResult:
        return cast(PipelineResult, cached_perception(text, lambda: self._run_inner(text, **kwargs)))

    def _run_inner(self, text: str, **kwargs: Any) -> PipelineResult:
        start = time.perf_counter()
        stages: dict[str, float] = {}

        try:
            t0 = time.perf_counter()
            self._validator.validate_text(text)
            stages["validate"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            normalized_text, norm_report = self._normalizer.normalize(text)
            stages["normalize"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            language, language_confidence = self._language_detector.detect(normalized_text)
            stages["detect_language"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            tokens = self._tokenizer.tokenize(normalized_text)
            stages["tokenize"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            sentences = self._structural_analyzer.analyze(normalized_text, tokens)
            stages["structural_analysis"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            linguistic = self._linguistic_orchestrator.analyze(normalized_text)
            stages["linguistic_analysis"] = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            metadata = self._metadata_extractor.extract(text, normalized_text)
            stages["metadata"] = (time.perf_counter() - t0) * 1000

            elapsed_ms = (time.perf_counter() - start) * 1000

            representation = CognitiveRepresentation(
                raw_text=text,
                normalized_text=normalized_text,
                language=language,
                language_confidence=language_confidence,
                tokens=tokens,
                sentences=sentences,
                linguistic=linguistic,
                metadata=metadata,
                validation=ValidationReport(
                    valid=len(norm_report.errors) == 0,
                    errors=list(norm_report.errors),
                    warnings=list(norm_report.warnings),
                ),
                processing_time_ms=elapsed_ms,
                extra=kwargs,
            )

            t0 = time.perf_counter()
            profile_result = cached_linguistic_profile(text, lambda: self._profile_builder.build(representation))
            stages["linguistic_intelligence"] = (time.perf_counter() - t0) * 1000
            representation.linguistic_profile = profile_result.profile

            t0 = time.perf_counter()
            if self._representation_builder is not None:
                builder = self._representation_builder
            else:
                from duplicate_question_app._semantic.representation_builder import RepresentationBuilder

                builder = RepresentationBuilder()
            semantic_representation = cached_semantic_representation(
                text, lambda: builder.build(profile_result.profile)
            )
            stages["semantic_representation"] = (time.perf_counter() - t0) * 1000
            representation.semantic_representation = semantic_representation

            total_elapsed = (time.perf_counter() - start) * 1000

            return PipelineResult(
                representation=representation,
                success=representation.validation.valid,
                timing_ms=total_elapsed,
                stages=stages,
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._logger.error("Pipeline failed after %.2fms: %s", elapsed_ms, exc)
            return PipelineResult(
                success=False,
                error=str(exc),
                timing_ms=elapsed_ms,
                stages=stages,
            )
