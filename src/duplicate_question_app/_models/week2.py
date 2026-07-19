"""Inference module for Week 2 classical ML models (TF-IDF + LR / TF-IDF + SVM)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack, spmatrix

from duplicate_question_app.config import AppPaths
from duplicate_question_app.preprocessing import normalize_question as _base_normalize


# TF-IDF models were trained on original text without abbreviation expansion.
def normalize_question(text):
    return _base_normalize(text, expand_abbrevs=False)


WEEK2_MODELS_DIR_NAME = "week2_models"


@dataclass(frozen=True)
class Week2ModelMetadata:
    model_label: str
    model_version: str
    decision_threshold: float
    threshold_source: str
    load_errors: tuple[str, ...]
    ready: bool
    is_transformer: bool = False
    device: str = "cpu"
    model_name: str = ""
    latency_ms: float = 0.0


def _get_week2_models_dir(paths: AppPaths) -> Path:
    return paths.models_dir / WEEK2_MODELS_DIR_NAME


def check_week2_artifacts(paths: AppPaths) -> dict[str, bool]:
    """Check which Week 2 model artifacts exist on disk."""
    models_dir = _get_week2_models_dir(paths)
    return {
        "tfidf": (models_dir / "tfidf_vectorizer.joblib").exists(),
        "logistic_regression": (models_dir / "logistic_regression.joblib").exists(),
        "linear_svm": (models_dir / "linear_svm.joblib").exists(),
    }


def is_week2_model(model_name: str) -> bool:
    return model_name in (
        "TF-IDF + Logistic Regression (Week 2)",
        "TF-IDF + Linear SVM (Week 2)",
    )


class Week2InferenceService:
    """Handles prediction for both TF-IDF + Logistic Regression and TF-IDF + Linear SVM."""

    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.models_dir = _get_week2_models_dir(paths)
        self._tfidf: Any | None = None
        self._lr_model: Any | None = None
        self._svm_model: Any | None = None
        self.device = "cpu"
        self.model_name = ""

    @property
    def threshold(self) -> float:
        return 0.5

    def _load_tfidf(self) -> Any:
        if self._tfidf is None:
            path = self.models_dir / "tfidf_vectorizer.joblib"
            if not path.exists():
                raise FileNotFoundError(f"TF-IDF vectorizer not found at {path}")
            self._tfidf = joblib.load(path)
        return self._tfidf

    def _load_lr(self) -> Any:
        if self._lr_model is None:
            path = self.models_dir / "logistic_regression.joblib"
            if not path.exists():
                raise FileNotFoundError(f"Logistic Regression model not found at {path}")
            self._lr_model = joblib.load(path)
        return self._lr_model

    def _load_svm(self) -> Any:
        if self._svm_model is None:
            path = self.models_dir / "linear_svm.joblib"
            if not path.exists():
                raise FileNotFoundError(f"Linear SVM model not found at {path}")
            self._svm_model = joblib.load(path)
        return self._svm_model

    def _extract_features(self, question1: str, question2: str) -> spmatrix:
        """Extract TF-IDF features exactly as done in the notebook."""
        q1 = normalize_question(question1)
        q2 = normalize_question(question2)
        tfidf = self._load_tfidf()
        q1_vec = tfidf.transform([q1])
        q2_vec = tfidf.transform([q2])
        return hstack([q1_vec, q2_vec])

    def _extract_features_batch(self, q1_list: list[str], q2_list: list[str]) -> spmatrix:
        """Extract TF-IDF features for a batch of question pairs."""
        tfidf = self._load_tfidf()
        q1_vec = tfidf.transform(q1_list)
        q2_vec = tfidf.transform(q2_list)
        return hstack([q1_vec, q2_vec])

    def predict_proba(self, question1: str, question2: str, model_name: str) -> tuple[float, float]:
        """Return (prob_non_duplicate, prob_duplicate)."""
        q1 = normalize_question(question1)
        q2 = normalize_question(question2)
        features = self._extract_features(q1, q2)

        if model_name == "TF-IDF + Logistic Regression (Week 2)":
            model = self._load_lr()
            proba = model.predict_proba(features)[0]
            return (float(proba[0]), float(proba[1]))
        elif model_name == "TF-IDF + Linear SVM (Week 2)":
            model = self._load_svm()
            decision = model.decision_function(features)[0]
            prob_dup = 1.0 / (1.0 + np.exp(-float(decision)))
            return (1.0 - prob_dup, prob_dup)
        else:
            raise ValueError(f"Unknown Week 2 model: {model_name}")

    def predict_single(self, question1: str, question2: str, model_name: str) -> dict[str, Any]:
        start_time = time.time()
        q1 = normalize_question(question1)
        q2 = normalize_question(question2)

        if not q1 or not q2:
            raise ValueError("Both question inputs are required.")

        features = self._extract_features(q1, q2)

        if model_name == "TF-IDF + Logistic Regression (Week 2)":
            model = self._load_lr()
            proba = model.predict_proba(features)[0]
            prob_duplicate = float(proba[1])
            prob_non_duplicate = float(proba[0])
            predicted_label = int(prob_duplicate >= 0.5)
            model_label = "TF-IDF + Logistic Regression (Week 2)"
        elif model_name == "TF-IDF + Linear SVM (Week 2)":
            model = self._load_svm()
            # LinearSVC doesn't have predict_proba, so use decision_function
            decision = model.decision_function(features)[0]
            # Convert decision function to probability-like score (sigmoid scaling)
            prob_duplicate = 1.0 / (1.0 + np.exp(-float(decision)))
            prob_non_duplicate = 1.0 - prob_duplicate
            predicted_label = int(prob_duplicate >= 0.5)
            model_label = "TF-IDF + Linear SVM (Week 2)"
        else:
            raise ValueError(f"Unknown Week 2 model: {model_name}")

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
            "threshold": 0.5,
            "model_label": model_label,
            "model_name": model_label,
            "device": "cpu",
            "latency_ms": latency_ms,
            "reason": None,
            "feature_breakdown": None,
        }

    def predict_batch(self, question_pairs: list[tuple[str, str]], model_name: str) -> pd.DataFrame:
        pairs = list(question_pairs)
        if not pairs:
            return pd.DataFrame()

        q1_list = [normalize_question(p[0]) for p in pairs]
        q2_list = [normalize_question(p[1]) for p in pairs]

        # Validate all non-empty
        for i, (q1, q2) in enumerate(zip(q1_list, q2_list, strict=False)):
            if not q1 or not q2:
                raise ValueError(f"Question pair at index {i} has empty text.")

        features = self._extract_features_batch(q1_list, q2_list)

        if model_name == "TF-IDF + Logistic Regression (Week 2)":
            model = self._load_lr()
            proba = model.predict_proba(features)
            prob_dup_arr = proba[:, 1]
            prob_non_dup_arr = proba[:, 0]
            model_label = "TF-IDF + Logistic Regression (Week 2)"
        elif model_name == "TF-IDF + Linear SVM (Week 2)":
            model = self._load_svm()
            decisions = model.decision_function(features)
            prob_dup_arr = 1.0 / (1.0 + np.exp(-decisions))
            prob_non_dup_arr = 1.0 - prob_dup_arr
            model_label = "TF-IDF + Linear SVM (Week 2)"
        else:
            raise ValueError(f"Unknown Week 2 model: {model_name}")

        predicted_labels = (prob_dup_arr >= 0.5).astype(int)
        confidences = np.maximum(prob_non_dup_arr, prob_dup_arr)

        results: list[dict[str, Any]] = []
        for i, (q1, q2) in enumerate(zip(q1_list, q2_list, strict=False)):
            results.append(
                {
                    "question1": q1,
                    "question2": q2,
                    "predicted_label": int(predicted_labels[i]),
                    "prediction": "Duplicate" if predicted_labels[i] == 1 else "Non-Duplicate",
                    "prob_non_duplicate": float(prob_non_dup_arr[i]),
                    "prob_duplicate": float(prob_dup_arr[i]),
                    "confidence": float(confidences[i]),
                    "threshold": 0.5,
                    "model_label": model_label,
                    "model_name": model_label,
                    "device": "cpu",
                    "latency_ms": 0.0,
                    "reason": None,
                    "feature_breakdown": None,
                }
            )

        return pd.DataFrame(results)
