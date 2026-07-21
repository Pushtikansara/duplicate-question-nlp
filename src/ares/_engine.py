from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ares._config import DEFAULT_MODEL, DEFAULT_THRESHOLD, DEFAULT_USE_REFLECTION
from ares._result import PredictionResult


@dataclass
class _ModelBundle:
    model: Any
    tokenizer: Any
    metadata: Any
    is_week2: bool = False
    service: Any = None


class ARES:
    def __init__(self) -> None:
        self._model_name: str | None = None
        self._threshold: float | None = None
        self._use_reflection: bool = DEFAULT_USE_REFLECTION
        self._bundle: _ModelBundle | None = None
        self._paths: Any = None
        self._device: Any = None
        self._reflection_engine: Any = None
        self._loaded = False

    def with_model(self, name: str) -> ARES:
        self._model_name = name
        return self

    def with_threshold(self, threshold: float) -> ARES:
        self._threshold = threshold
        return self

    def with_reflection(self, enabled: bool = True) -> ARES:
        self._use_reflection = enabled
        return self

    def _lazy_load(self) -> None:
        if self._loaded:
            return

        from duplicate_question_app._config.settings import get_app_paths, get_config
        from duplicate_question_app._models.week2 import is_week2_model
        from duplicate_question_app.utils.device import resolve_device

        self._model_name = self._model_name or get_config("app").get("default_model", DEFAULT_MODEL)
        self._threshold = (
            self._threshold
            if self._threshold is not None
            else get_config("inference").get("default_threshold", DEFAULT_THRESHOLD)
        )

        self._paths = get_app_paths()
        self._device = resolve_device()

        if is_week2_model(self._model_name):
            from duplicate_question_app._models.week2 import Week2InferenceService

            svc = Week2InferenceService(self._paths)
            self._bundle = _ModelBundle(
                model=None,
                tokenizer=None,
                metadata=None,
                is_week2=True,
                service=svc,
            )
        else:
            from duplicate_question_app._inference.transformer import (
                DuplicateQuestionInferenceService,
                load_model_and_tokenizer,
            )

            model, tokenizer, metadata = load_model_and_tokenizer(self._paths, model_version=self._model_name)
            svc = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
            self._bundle = _ModelBundle(
                model=model,
                tokenizer=tokenizer,
                metadata=metadata,
                service=svc,
            )

        if self._use_reflection:
            from duplicate_question_app._reflection.reflection_engine import ReflectionEngine

            self._reflection_engine = ReflectionEngine()

        self._loaded = True

    def predict(self, question1: str, question2: str) -> PredictionResult:
        self._lazy_load()

        start = time.perf_counter()
        raw = self._bundle.service.predict_single(question1, question2)
        elapsed_ms = (time.perf_counter() - start) * 1000

        result = PredictionResult(
            predicted_label=raw["predicted_label"],
            prediction=raw["prediction"],
            confidence=raw["confidence"],
            prob_duplicate=raw["prob_duplicate"],
            prob_non_duplicate=raw["prob_non_duplicate"],
            model_name=raw.get("model_label", self._model_name or "unknown"),
            latency_ms=elapsed_ms,
            raw=raw,
        )

        if self._use_reflection and self._reflection_engine:
            try:
                ref = self._reflection_engine.reflect(prediction=raw)
                result.trust_score = ref.trust_score
                result.trust_level = ref.trust_level.value if ref.trust_level else None
                result.risk_level = ref.risk_level.value if ref.risk_level else None
                result.human_review_required = ref.human_review_required
                result.recommendations = [r.value for r in ref.recommendations]
                result.explanations = ref.metadata.get("explainability", {})
            except Exception:
                pass

        return result

    def predict_batch(self, pairs: list[tuple[str, str]]) -> list[PredictionResult]:
        return [self.predict(q1, q2) for q1, q2 in pairs]
