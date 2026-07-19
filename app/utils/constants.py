from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.config import get_app_paths

PATHS = get_app_paths(PROJECT_ROOT)

_model_cache: dict[str, Any] = {}


def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    candidate_pairs = [("q1", "q2"), ("question1", "question2"), ("sentence1", "sentence2")]
    for col1, col2 in candidate_pairs:
        if col1 in df.columns and col2 in df.columns:
            return col1, col2
    return None


def get_model_prediction(service: Any, selected_model: str, question1: str, question2: str) -> dict[str, Any]:
    from duplicate_question_app.config import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app.week2_inference import is_week2_model
    from duplicate_question_app.embedding_models import get_ensemble_prediction, predict_with_sentence_transformer

    if is_week2_model(selected_model):
        return service.predict_single(question1, question2, selected_model)
    elif is_ensemble_model(selected_model):
        return get_ensemble_prediction(question1, question2)
    elif is_new_embedding_model(selected_model):
        return predict_with_sentence_transformer(selected_model, question1, question2)
    else:
        return service.predict_single(question1, question2)


def run_batch_prediction(service: Any, selected_model: str, question_pairs: list[tuple[str, str]]) -> pd.DataFrame:
    from duplicate_question_app.config import is_ensemble_model, is_new_embedding_model
    from duplicate_question_app.week2_inference import is_week2_model
    from duplicate_question_app.embedding_models import get_ensemble_prediction, predict_batch_sentence_transformer

    if is_week2_model(selected_model):
        return service.predict_batch(question_pairs, selected_model)
    else:
        if is_ensemble_model(selected_model):
            results_list = []
            for q1, q2 in question_pairs:
                r = get_ensemble_prediction(q1, q2)
                results_list.append(r)
            return pd.DataFrame(results_list)
        elif is_new_embedding_model(selected_model):
            return pd.DataFrame(
                predict_batch_sentence_transformer(selected_model, question_pairs, batch_size=64)
            )
        else:
            results_list = []
            for q1, q2 in question_pairs:
                r = service.predict_single(q1, q2)
                results_list.append(r)
            return pd.DataFrame(results_list)
