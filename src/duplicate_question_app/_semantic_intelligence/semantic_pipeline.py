from __future__ import annotations

import time
from typing import Any, cast

from duplicate_question_app._inference.cache import (
    cached_semantic_representation,
)
from duplicate_question_app._perception.pipeline import PerceptionPipeline
from duplicate_question_app._profiling import profile
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.engine import SemanticIntelligenceEngine
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class SemanticPipelineService:
    def __init__(
        self,
        perception_pipeline: PerceptionPipeline | None = None,
        semantic_engine: SemanticIntelligenceEngine | None = None,
    ):
        self._pipeline = perception_pipeline or PerceptionPipeline()
        self._engine = semantic_engine or SemanticIntelligenceEngine()

    @profile("analyze_question")
    def analyze_question(self, text: str) -> SemanticRepresentation | None:
        rep = cached_semantic_representation(text, lambda: self._build_representation(text))
        if rep is not None:
            return cast(SemanticRepresentation, rep)
        return None

    def _build_representation(self, text: str) -> SemanticRepresentation | None:
        result = self._pipeline.run(text)
        if not result.success or result.representation is None:
            return None
        sr = result.representation.semantic_representation
        if sr is not None:
            sr.reasoning_metadata["perception_timing_ms"] = result.timing_ms
            sr.reasoning_metadata["perception_stages"] = result.stages
        return cast(SemanticRepresentation, sr)

    @profile("assess_pair")
    def assess(
        self,
        question_a: str,
        question_b: str,
        use_cache: bool = True,
    ) -> tuple[SemanticAssessment | None, dict[str, Any]]:
        metadata: dict[str, Any] = {"stages": {}, "cache_hits": {}}
        t0 = time.perf_counter()

        t_start = time.perf_counter()
        rep_a = self.analyze_question(question_a) if use_cache else self._build_representation(question_a)
        metadata["stages"]["pipeline_a_ms"] = (time.perf_counter() - t_start) * 1000

        t_start = time.perf_counter()
        rep_b = self.analyze_question(question_b) if use_cache else self._build_representation(question_b)
        metadata["stages"]["pipeline_b_ms"] = (time.perf_counter() - t_start) * 1000

        if rep_a is None or rep_b is None:
            metadata["error"] = "Failed to build semantic representation for one or both questions"
            return None, metadata

        t_start = time.perf_counter()
        assessment = self._engine.assess(rep_a, rep_b)
        metadata["stages"]["semantic_engine_ms"] = (time.perf_counter() - t_start) * 1000

        metadata["total_ms"] = (time.perf_counter() - t0) * 1000
        metadata["has_assessment"] = True

        return assessment, metadata

    @profile("assess_with_reps")
    def assess_with_representations(
        self,
        question_a: str,
        question_b: str,
        use_cache: bool = True,
    ) -> tuple[SemanticAssessment | None, SemanticRepresentation | None, SemanticRepresentation | None, dict[str, Any]]:
        metadata: dict[str, Any] = {"stages": {}, "cache_hits": {}}
        t0 = time.perf_counter()

        t_start = time.perf_counter()
        rep_a = self.analyze_question(question_a) if use_cache else self._build_representation(question_a)
        metadata["stages"]["pipeline_a_ms"] = (time.perf_counter() - t_start) * 1000

        t_start = time.perf_counter()
        rep_b = self.analyze_question(question_b) if use_cache else self._build_representation(question_b)
        metadata["stages"]["pipeline_b_ms"] = (time.perf_counter() - t_start) * 1000

        if rep_a is None or rep_b is None:
            metadata["error"] = "Failed to build semantic representation for one or both questions"
            return None, rep_a, rep_b, metadata

        t_start = time.perf_counter()
        assessment = self._engine.assess(rep_a, rep_b)
        metadata["stages"]["semantic_engine_ms"] = (time.perf_counter() - t_start) * 1000

        metadata["total_ms"] = (time.perf_counter() - t0) * 1000
        metadata["has_assessment"] = True

        return assessment, rep_a, rep_b, metadata
