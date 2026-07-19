from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from duplicate_question_app.artifacts import load_week4_threshold_analysis
from duplicate_question_app.config import (
    AppPaths,
    ModelDirectoryStatus,
    get_config,
    is_transformer_model,
    resolve_model_selection,
)
from duplicate_question_app.preprocessing import normalize_question
from duplicate_question_app.week2_inference import Week2InferenceService, is_week2_model

DEFAULT_MAX_LENGTH = get_config("inference").get("max_length", 128)


@dataclass(frozen=True)
class ModelMetadata:
    model_dir: Path
    model_label: str
    model_version: str
    decision_threshold: float
    threshold_source: str
    device: str
    fallback_reason: str | None
    load_errors: tuple[str, ...]
    cache_key: str
    model_name: str = ""


# DistilBERT models were fine-tuned on original (non-expanded) text.
# Abbreviation expansion would change token distributions they were trained on.
_norm = lambda text: normalize_question(text, expand_abbrevs=False)


def _resolve_threshold(paths: AppPaths) -> tuple[float, str]:
    threshold_df = load_week4_threshold_analysis(paths)
    default_threshold = get_config("inference").get("default_threshold", 0.5)
    if threshold_df.empty or "F1" not in threshold_df.columns or "Threshold" not in threshold_df.columns:
        return default_threshold, f"Default threshold {default_threshold:.2f} (Week 4 threshold analysis unavailable)"

    best_f1 = threshold_df["F1"].max()
    best_candidates = threshold_df.loc[threshold_df["F1"] == best_f1, "Threshold"].astype(float)
    best_threshold = float(best_candidates.max())
    return best_threshold, "Best F1 threshold from `results/week4_improvement/threshold_analysis.csv`"


def _load_hugging_face_artifacts(model_dir: Path) -> tuple[AutoModelForSequenceClassification, AutoTokenizer]:
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    return model, tokenizer


def _build_metadata(
    status: ModelDirectoryStatus,
    model_version: str,
    device: str,
    fallback_reason: str | None,
    load_errors: tuple[str, ...],
    cache_key: str,
    paths: AppPaths,
) -> ModelMetadata:
    from duplicate_question_app._config.loader import get_config as _get_inf_config
    _inf_cfg = _get_inf_config("inference")
    _default_th = _inf_cfg.get("default_threshold", 0.5)

    if model_version == "week4":
        decision_threshold, threshold_source = _resolve_threshold(paths)
    else:
        decision_threshold = _default_th
        threshold_source = f"Default threshold {_default_th:.2f} for baseline models"

    return ModelMetadata(
        model_dir=status.model_dir,
        model_label=status.label,
        model_version=model_version,
        decision_threshold=decision_threshold,
        threshold_source=threshold_source,
        device=device,
        fallback_reason=fallback_reason,
        load_errors=load_errors,
        cache_key=cache_key,
        model_name=status.label,
    )


def _resolve_device() -> str:
    """Force CPU to avoid CUDA OOM in constrained environments."""
    inf_cfg = get_config("inference")
    return inf_cfg.get("default_device", "cpu")


def load_model_and_tokenizer(paths: AppPaths, model_version: str | None = None) -> tuple[AutoModelForSequenceClassification, AutoTokenizer, ModelMetadata]:
    resolution = resolve_model_selection(paths)
    device = _resolve_device()

    if model_version and not is_transformer_model(model_version):
        raise ValueError(f"Model '{model_version}' does not support live inference (not a transformer model).")

    candidates: list[tuple[str, ModelDirectoryStatus, str | None]] = []

    if model_version == "Improved DistilBERT (Week 4)" or model_version is None:
        if resolution.week4.ready:
            candidates.append(("week4", resolution.week4, None))

    if model_version == "DistilBERT (Week 3)" or (model_version is None and not candidates):
        if resolution.week3.ready:
            fallback = None if model_version else resolution.fallback_reason
            candidates.append(("week3", resolution.week3, fallback))

    # If the user explicitly requested a model that isn't ready, add a fallback
    if not candidates and model_version:
        if model_version == "Improved DistilBERT (Week 4)" and resolution.week3.ready:
            candidates.append(("week3", resolution.week3, resolution.fallback_reason))
        elif model_version == "DistilBERT (Week 3)" and resolution.week4.ready:
            candidates.append(("week4", resolution.week4, None))

    if not candidates:
        if model_version:
            raise FileNotFoundError(f"Model '{model_version}' artifacts are not available or incomplete.")
        week4_issues = ", ".join(resolution.week4.issues) or "unavailable"
        week3_issues = ", ".join(resolution.week3.issues) or "unavailable"
        raise FileNotFoundError(
            "No loadable model artifacts were found. "
            f"Week 4: {week4_issues}. Week 3: {week3_issues}."
        )

    load_errors: list[str] = []
    for ver, status, fallback_reason in candidates:
        try:
            model, tokenizer = _load_hugging_face_artifacts(status.model_dir)
            model = model.to(device)
            model.eval()
            metadata = _build_metadata(
                status=status,
                model_version=ver,
                device=device,
                fallback_reason=fallback_reason,
                load_errors=tuple(load_errors),
                cache_key=resolution.cache_key,
                paths=paths,
            )
            return model, tokenizer, metadata
        except Exception as exc:
            load_errors.append(f"{status.label}: {exc}")

    raise RuntimeError(
        "Unable to load any available model. "
        + " | ".join(load_errors)
    )


class DuplicateQuestionInferenceService:
    def __init__(
        self,
        model: AutoModelForSequenceClassification,
        tokenizer: AutoTokenizer,
        metadata: ModelMetadata,
        max_length: int = DEFAULT_MAX_LENGTH,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.metadata = metadata
        self.max_length = max_length

    @property
    def device(self) -> str:
        return self.metadata.device

    @property
    def model_name(self) -> str:
        return self.metadata.model_label

    @property
    def threshold(self) -> float:
        return self.metadata.decision_threshold

    def predict_proba(self, question1: str, question2: str) -> tuple[float, float]:
        """Return (prob_non_duplicate, prob_duplicate)."""
        q1 = _norm(question1)
        q2 = _norm(question2)

        inputs = self.tokenizer(
            q1,
            q2,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.metadata.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)[0]

        return (float(probabilities[0].item()), float(probabilities[1].item()))

    def predict_single(self, question1: str, question2: str) -> dict[str, object]:
        start_time = time.time()
        q1 = _norm(question1)
        q2 = _norm(question2)

        if not q1 or not q2:
            raise ValueError("Both question inputs are required.")

        inputs = self.tokenizer(
            q1,
            q2,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.metadata.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)[0]

        prob_non_duplicate = float(probabilities[0].item())
        prob_duplicate = float(probabilities[1].item())
        predicted_label = int(prob_duplicate >= self.metadata.decision_threshold)
        confidence = max(prob_non_duplicate, prob_duplicate)

        latency_ms = (time.time() - start_time) * 1000

        return {
            "question1": q1,
            "question2": q2,
            "predicted_label": predicted_label,
            "prediction": "Duplicate" if predicted_label == 1 else "Non-Duplicate",
            "prob_non_duplicate": prob_non_duplicate,
            "prob_duplicate": prob_duplicate,
            "confidence": confidence,
            "threshold": self.metadata.decision_threshold,
            "model_label": self.metadata.model_label,
            "model_name": self.metadata.model_label,
            "device": self.metadata.device,
            "latency_ms": latency_ms,
            "reason": None,
            "feature_breakdown": None,
        }

    def predict_batch(self, question_pairs: Iterable[tuple[str, str]]) -> pd.DataFrame:
        pairs = list(question_pairs)
        if not pairs:
            return pd.DataFrame()

        normalized_pairs: list[tuple[str, str]] = []
        for question1, question2 in pairs:
            q1 = _norm(question1)
            q2 = _norm(question2)
            if not q1 or not q2:
                raise ValueError("All question pairs must have non-empty question1 and question2 text.")
            normalized_pairs.append((q1, q2))

        batch_size = 32
        results: list[dict[str, object]] = []

        for start in range(0, len(normalized_pairs), batch_size):
            batch = normalized_pairs[start : start + batch_size]
            q1_list = [item[0] for item in batch]
            q2_list = [item[1] for item in batch]

            inputs = self.tokenizer(
                q1_list,
                q2_list,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            inputs = {key: value.to(self.metadata.device) for key, value in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1).detach().cpu().numpy()

            for (q1, q2), (prob_non_duplicate, prob_duplicate) in zip(batch, probabilities):
                prob_non_duplicate_f = float(prob_non_duplicate)
                prob_duplicate_f = float(prob_duplicate)
                predicted_label = int(prob_duplicate_f >= self.metadata.decision_threshold)
                confidence = max(prob_non_duplicate_f, prob_duplicate_f)
                results.append(
                    {
                        "question1": q1,
                        "question2": q2,
                        "predicted_label": predicted_label,
                        "prediction": "Duplicate" if predicted_label == 1 else "Non-Duplicate",
                        "prob_non_duplicate": prob_non_duplicate_f,
                        "prob_duplicate": prob_duplicate_f,
                        "confidence": confidence,
                        "threshold": self.metadata.decision_threshold,
                        "model_label": self.metadata.model_label,
                        "model_name": self.metadata.model_label,
                        "device": self.metadata.device,
                        "latency_ms": 0.0,
                        "reason": None,
                        "feature_breakdown": None,
                    }
                )

        return pd.DataFrame(results)
