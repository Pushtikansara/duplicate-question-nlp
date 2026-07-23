from __future__ import annotations

import time
from typing import Any

from ares._result import PredictionResult

_SUPPORTED_MODEL_TYPES = frozenset({
    "classical-ml",
    "transformer",
    "bi-encoder",
    "cross-encoder",
    "ensemble",
})


def _get_paths() -> Any:
    from duplicate_question_app._config.settings import get_app_paths

    return get_app_paths()


def _get_device() -> str:
    from duplicate_question_app.utils.device import resolve_device

    return resolve_device()


def _lookup_model(model_name: str) -> Any:
    from duplicate_question_app._models.registry import find_registry_entry

    paths = _get_paths()
    entry = find_registry_entry(model_name, paths)
    if entry is None:
        raise ValueError(
            f"Unknown model: '{model_name}'. "
            f"Use InferenceDispatcher.list_models() to see available models."
        )
    return entry, paths


def _run_classical_ml(model_name: str, q1: str, q2: str, paths: Any) -> dict[str, Any]:
    from duplicate_question_app._models.week2 import Week2InferenceService

    svc = Week2InferenceService(paths)
    return svc.predict_single(q1, q2, model_name)


def _run_transformer(
    model_name: str,
    q1: str,
    q2: str,
    paths: Any,
    device: str,
    internal_id: str,
) -> dict[str, Any]:
    from duplicate_question_app._config.settings import inspect_model_dir, get_config
    from duplicate_question_app._inference.transformer import (
        DuplicateQuestionInferenceService,
        ModelMetadata,
        _load_hugging_face_artifacts,
    )

    model_dir = (
        paths.week4_model_dir
        if internal_id == "week4"
        else paths.week3_model_dir
    )

    status = inspect_model_dir(model_dir, model_name)
    if not status.ready:
        issues = "; ".join(status.issues)
        raise ValueError(
            f"Model '{model_name}' artifacts are not available at {model_dir}. "
            f"Details: {issues}"
        )

    model, tokenizer = _load_hugging_face_artifacts(model_dir)
    model = model.to(device)
    model.eval()

    metadata = ModelMetadata(
        model_dir=model_dir,
        model_label=model_name,
        model_version=internal_id,
        decision_threshold=get_config("inference").get("default_threshold", 0.5),
        threshold_source=f"Default threshold for {model_name}",
        device=device,
        fallback_reason=None,
        load_errors=(),
        cache_key=internal_id,
        model_name=model_name,
    )

    svc = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    return svc.predict_single(q1, q2)


def _run_sentence_transformer(model_name: str, q1: str, q2: str) -> dict[str, Any]:
    from duplicate_question_app._models.embeddings import predict_with_sentence_transformer

    return predict_with_sentence_transformer(model_name, q1, q2)


def _run_ensemble(q1: str, q2: str, paths: Any) -> dict[str, Any]:
    from duplicate_question_app._models.embeddings import get_ensemble_prediction

    return get_ensemble_prediction(q1, q2, paths)


class InferenceDispatcher:
    @staticmethod
    def predict(
        model_name: str,
        question1: str,
        question2: str,
        threshold: float | None = None,
    ) -> PredictionResult:
        entry, paths = _lookup_model(model_name)
        model_type = entry.model_type

        if model_type not in _SUPPORTED_MODEL_TYPES:
            raise ValueError(
                f"Model '{model_name}' has unsupported type '{model_type}'. "
                f"Supported types: {', '.join(sorted(_SUPPORTED_MODEL_TYPES))}."
            )

        device = _get_device()
        start = time.perf_counter()

        if model_type == "classical-ml":
            raw = _run_classical_ml(model_name, question1, question2, paths)
        elif model_type == "transformer":
            raw = _run_transformer(model_name, question1, question2, paths, device, entry.internal_id)
        elif model_type in ("bi-encoder", "cross-encoder"):
            raw = _run_sentence_transformer(model_name, question1, question2)
        elif model_type == "ensemble":
            raw = _run_ensemble(question1, question2, paths)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return PredictionResult(
            predicted_label=raw["predicted_label"],
            prediction=raw["prediction"],
            confidence=raw["confidence"],
            prob_duplicate=raw["prob_duplicate"],
            prob_non_duplicate=raw["prob_non_duplicate"],
            model_name=raw.get("model_label", model_name),
            latency_ms=elapsed_ms,
            raw=raw,
        )

    @staticmethod
    def validate_model(model_name: str) -> None:
        entry, _ = _lookup_model(model_name)
        model_type = entry.model_type
        if model_type not in _SUPPORTED_MODEL_TYPES:
            raise ValueError(
                f"Model '{model_name}' has unsupported type '{model_type}'. "
                f"Supported types: {', '.join(sorted(_SUPPORTED_MODEL_TYPES))}."
            )

    @staticmethod
    def list_models() -> list[str]:
        from duplicate_question_app._models.registry import build_registry

        return [e.display_name for e in build_registry()]


predict = InferenceDispatcher.predict
