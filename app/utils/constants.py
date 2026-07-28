from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def get_model_prediction(service: Any, selected_model: str, question1: str, question2: str) -> dict[str, Any]:
    from ares.inference.dispatcher import InferenceDispatcher

    result = InferenceDispatcher.predict(
        model_name=selected_model,
        question1=question1,
        question2=question2,
    )

    base_result = {
        "question1": question1,
        "question2": question2,
        "predicted_label": result.predicted_label,
        "prediction": result.prediction,
        "confidence": result.confidence,
        "prob_duplicate": result.prob_duplicate,
        "prob_non_duplicate": result.prob_non_duplicate,
        "model_label": result.model_name,
        "model_name": result.model_name,
        "latency_ms": result.latency_ms,
        "threshold": result.threshold,
        "selected_model": result.selected_model,
        "executed_model": result.executed_model,
        "backend": result.backend,
        "artifact_path": result.artifact_path,
        "tokenizer": result.tokenizer,
        "inference_function": result.inference_function,
        "execution_time_ms": result.execution_time_ms,
        "raw_logits": result.raw_logits,
        "softmax": result.softmax,
        "predicted_class_id": result.predicted_class_id,
        "label_mapping": result.label_mapping,
        "final_label": result.final_label,
        "device": "cpu",
        "reason": None,
        "feature_breakdown": {},
        "base_prediction": result.prediction,
        "final_prediction": result.prediction,
        "prediction_overridden": False,
        "override_reason": None,
        "override_confidence_delta": 0,
    }
    return base_result


def run_batch_prediction(service: Any, selected_model: str, question_pairs: list[tuple[str, str]]) -> pd.DataFrame:
    from ares.inference.dispatcher import InferenceDispatcher

    rows = []
    for q1, q2 in question_pairs:
        result = InferenceDispatcher.predict(
            model_name=selected_model,
            question1=q1,
            question2=q2,
        )
        rows.append(
            {
                "question1": q1,
                "question2": q2,
                "predicted_label": result.predicted_label,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "prob_duplicate": result.prob_duplicate,
                "prob_non_duplicate": result.prob_non_duplicate,
                "model_label": result.model_name,
                "latency_ms": result.latency_ms,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# PATHS — lazily initialised once on first attribute access.
# Every module that does "from app.utils.constants import PATHS" receives a
# fully resolved AppPaths instance.  Module-level __getattr__ (PEP 562)
# ensures the value is computed exactly once and cached thereafter.
# ---------------------------------------------------------------------------
_PATHS: Any | None = None
_model_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    if name == "PATHS":
        global _PATHS
        if _PATHS is None:
            from duplicate_question_app._config.settings import get_app_paths

            _PATHS = get_app_paths(PROJECT_ROOT)
        return _PATHS
    if name == "get_app_paths":
        from duplicate_question_app._config.settings import get_app_paths

        return get_app_paths
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def _get_semantic_pipeline():
    from duplicate_question_app._semantic_intelligence.semantic_pipeline import (
        SemanticPipelineService,
    )

    return SemanticPipelineService()


def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    candidates = [
        ("q1", "q2"),
        ("question1", "question2"),
        ("sentence1", "sentence2"),
        ("text1", "text2"),
    ]
    for col1, col2 in candidates:
        if col1 in df.columns and col2 in df.columns:
            return col1, col2
    return None


def _get_assessment_dict(assessment) -> dict:
    if assessment is None:
        return {}
    if hasattr(assessment, "to_dict"):
        return assessment.to_dict()
    return {}


def _get_decision_fusion(mode: str):
    from duplicate_question_app._semantic_intelligence.fusion import (
        DecisionFusion,
        FusionStrategy,
    )

    strategy_map: dict[str, FusionStrategy] = {
        "cross_encoder_only": FusionStrategy.CROSS_ENCODER_ONLY,
        "semantic_only": FusionStrategy.SEMANTIC_ONLY,
        "fusion": FusionStrategy.FUSION,
        "cross_encoder_dominant": FusionStrategy.CROSS_ENCODER_DOMINANT,
        "semantic_dominant": FusionStrategy.SEMANTIC_DOMINANT,
        "confidence_weighted": FusionStrategy.CONFIDENCE_WEIGHTED,
        "adaptive": FusionStrategy.ADAPTIVE,
        "learned_weighting": FusionStrategy.LEARNED_WEIGHTING,
    }
    strategy = strategy_map.get(mode, FusionStrategy.FUSION)
    return DecisionFusion(strategy=strategy)


def _get_prediction_mode() -> str:
    import streamlit as st

    return st.session_state.get("prediction_mode", "fusion")
