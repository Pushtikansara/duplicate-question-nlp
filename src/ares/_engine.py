from __future__ import annotations

import time
from typing import Any

from ares._config import DEFAULT_MODEL, DEFAULT_THRESHOLD, DEFAULT_USE_REFLECTION
from ares._result import PredictionResult
from ares.inference.dispatcher import InferenceDispatcher


class ARES:
    def __init__(self) -> None:
        self._model_name: str | None = None
        self._threshold: float | None = None
        self._use_reflection: bool = DEFAULT_USE_REFLECTION
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

        from duplicate_question_app._config.settings import get_config

        self._model_name = self._model_name or get_config("app").get("default_model", DEFAULT_MODEL)
        self._threshold = (
            self._threshold
            if self._threshold is not None
            else get_config("inference").get("default_threshold", DEFAULT_THRESHOLD)
        )

        InferenceDispatcher.validate_model(self._model_name)

        if self._use_reflection:
            from duplicate_question_app._reflection.reflection_engine import ReflectionEngine

            self._reflection_engine = ReflectionEngine()

        self._loaded = True

    def predict(self, question1: str, question2: str) -> PredictionResult:
        self._lazy_load()

        assert self._model_name is not None
        result = InferenceDispatcher.predict(
            model_name=self._model_name,
            question1=question1,
            question2=question2,
        )

        if self._use_reflection and self._reflection_engine:
            try:
                ref = self._reflection_engine.reflect(
                    prediction={
                        "predicted_label": result.predicted_label,
                        "prediction": result.prediction,
                        "confidence": result.confidence,
                        "prob_duplicate": result.prob_duplicate,
                        "prob_non_duplicate": result.prob_non_duplicate,
                    }
                )
                result.trust_score = max(0.0, min(1.0, ref.trust_score if ref.trust_score is not None else 0.0))
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

    @staticmethod
    def list_models() -> list[str]:
        return InferenceDispatcher.list_models()
