"""Application constants and utility functions.

This module provides:
- PATHS: Centralized path configuration
- _model_cache: Cache for loaded model services
- Helper functions for model prediction dispatch
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app._config.settings import get_app_paths

PATHS = get_app_paths(PROJECT_ROOT)

from app.services.cache import get_cache

_cache_manager = get_cache()
_model_cache: dict[str, Any] = _cache_manager._model_cache  # type: ignore[attr-defined]


def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    """Detect question columns in a DataFrame.

    Supports q1/q2, question1/question2, sentence1/sentence2 column naming.
    """
    candidate_pairs = [
        ("q1", "q2"),
        ("question1", "question2"),
        ("sentence1", "sentence2"),
    ]
    for col1, col2 in candidate_pairs:
        if col1 in df.columns and col2 in df.columns:
            return col1, col2
    return None


def get_model_prediction(service: Any, selected_model: str, question1: str, question2: str) -> dict[str, Any]:
    """Dispatch a single prediction to the appropriate model service.

    Args:
        service: The inference service (None for embedding/ensemble models)
        selected_model: Name of the selected model
        question1: First question text
        question2: Second question text

    Returns:
        Dict with prediction results
    """
    from duplicate_question_app._config.settings import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app._models.embeddings import get_ensemble_prediction, predict_with_sentence_transformer
    from duplicate_question_app._models.week2 import is_week2_model

    if is_week2_model(selected_model):
        return service.predict_single(question1, question2, selected_model)
    elif is_ensemble_model(selected_model):
        return get_ensemble_prediction(question1, question2)
    elif is_new_embedding_model(selected_model):
        return predict_with_sentence_transformer(selected_model, question1, question2)
    else:
        return service.predict_single(question1, question2)


def run_batch_prediction(service: Any, selected_model: str, question_pairs: list[tuple[str, str]]) -> pd.DataFrame:
    """Run batch prediction for a list of question pairs.

    Args:
        service: The inference service (None for embedding/ensemble models)
        selected_model: Name of the selected model
        question_pairs: List of (q1, q2) tuples

    Returns:
        DataFrame with prediction results
    """
    from duplicate_question_app._config.settings import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app._models.embeddings import (
        get_ensemble_prediction,
        predict_batch_sentence_transformer,
    )
    from duplicate_question_app._models.week2 import is_week2_model

    if is_week2_model(selected_model):
        return service.predict_batch(question_pairs, selected_model)

    if is_ensemble_model(selected_model):
        results_list = []
        for q1, q2 in question_pairs:
            r = get_ensemble_prediction(q1, q2)
            results_list.append(r)
        return pd.DataFrame(results_list)

    if is_new_embedding_model(selected_model):
        return pd.DataFrame(predict_batch_sentence_transformer(selected_model, question_pairs, batch_size=64))

    # Transformer model batch prediction
    results_list = []
    for q1, q2 in question_pairs:
        r = service.predict_single(q1, q2)
        results_list.append(r)
    return pd.DataFrame(results_list)
