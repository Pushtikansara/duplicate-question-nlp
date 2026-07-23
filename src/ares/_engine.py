from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ares._config import DEFAULT_MODEL, DEFAULT_THRESHOLD, DEFAULT_USE_REFLECTION
from ares._result import PredictionResult


@dataclass
class _ModelBundle:
    service: Any
    model_type: str
    model: Any = None
    tokenizer: Any = None
    metadata: Any = None


_SUPPORTED_MODEL_TYPES = frozenset({
    "classical-ml",
    "transformer",
    "bi-encoder",
    "cross-encoder",
    "ensemble",
})


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
        from duplicate_question_app._models.registry import find_registry_entry
        from duplicate_question_app.utils.device import resolve_device

        self._model_name = self._model_name or get_config("app").get("default_model", DEFAULT_MODEL)
        self._threshold = (
            self._threshold
            if self._threshold is not None
            else get_config("inference").get("default_threshold", DEFAULT_THRESHOLD)
        )

        self._paths = get_app_paths()
        self._device = resolve_device()

        entry = find_registry_entry(self._model_name, self._paths)
        if entry is None:
            raise ValueError(
                f"Unknown model: '{self._model_name}'. "
                f"Use ARES.list_models() to see available models."
            )

        model_type = entry.model_type
        if model_type not in _SUPPORTED_MODEL_TYPES:
            raise ValueError(
                f"Model '{self._model_name}' has unsupported type '{model_type}'. "
                f"Supported types: {', '.join(sorted(_SUPPORTED_MODEL_TYPES))}."
            )

        if model_type == "classical-ml":
            from duplicate_question_app._models.week2 import Week2InferenceService

            svc: Any = Week2InferenceService(self._paths)
            self._bundle = _ModelBundle(
                service=svc,
                model_type=model_type,
            )

        elif model_type == "transformer":
            from duplicate_question_app._config.settings import inspect_model_dir
            from duplicate_question_app._inference.transformer import (
                DuplicateQuestionInferenceService,
                ModelMetadata,
                _load_hugging_face_artifacts,
            )

            model_dir = (
                self._paths.week4_model_dir
                if entry.internal_id == "week4"
                else self._paths.week3_model_dir
            )

            status = inspect_model_dir(model_dir, self._model_name)
            if not status.ready:
                issues = "; ".join(status.issues)
                raise ValueError(
                    f"Model '{self._model_name}' artifacts are not available at {model_dir}. "
                    f"Details: {issues}"
                )

            model, tokenizer = _load_hugging_face_artifacts(model_dir)
            model = model.to(self._device)
            model.eval()

            metadata = ModelMetadata(
                model_dir=model_dir,
                model_label=self._model_name,
                model_version=entry.internal_id,
                decision_threshold=get_config("inference").get("default_threshold", 0.5),
                threshold_source=f"Default threshold for {self._model_name}",
                device=self._device,
                fallback_reason=None,
                load_errors=(),
                cache_key=entry.internal_id,
                model_name=self._model_name,
            )

            svc = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
            self._bundle = _ModelBundle(
                model=model,
                tokenizer=tokenizer,
                metadata=metadata,
                service=svc,
                model_type=model_type,
            )

        elif model_type in ("bi-encoder", "cross-encoder"):
            from duplicate_question_app._models.embeddings import predict_with_sentence_transformer

            svc = _CallableService(
                predict_with_sentence_transformer,
                model_name=self._model_name,
            )
            self._bundle = _ModelBundle(service=svc, model_type=model_type)

        elif model_type == "ensemble":
            from duplicate_question_app._models.embeddings import get_ensemble_prediction

            svc = _CallableService(
                get_ensemble_prediction,
                paths=self._paths,
            )
            self._bundle = _ModelBundle(service=svc, model_type=model_type)

        if self._use_reflection:
            from duplicate_question_app._reflection.reflection_engine import ReflectionEngine

            self._reflection_engine = ReflectionEngine()

        self._loaded = True

    def predict(self, question1: str, question2: str) -> PredictionResult:
        self._lazy_load()

        start = time.perf_counter()
        assert self._bundle is not None

        if self._bundle.model_type == "classical-ml":
            raw = self._bundle.service.predict_single(question1, question2, self._model_name)
        elif self._bundle.model_type == "transformer":
            raw = self._bundle.service.predict_single(question1, question2)
        else:
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
        from duplicate_question_app._models.registry import build_registry

        return [e.display_name for e in build_registry()]


class _CallableService:
    def __init__(self, func: Any, **fixed_kwargs: Any) -> None:
        self._func = func
        self._fixed_kwargs = fixed_kwargs

    def predict_single(self, question1: str, question2: str) -> dict[str, Any]:
        return self._func(question1, question2, **self._fixed_kwargs)
