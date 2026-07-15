"""Page modules for the DQD Streamlit application.

Each page is a self-contained module that receives shared dependencies
via its render function parameters. This keeps app.py lightweight and
allows individual page files to stay under 400 lines.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import streamlit as st

from duplicate_question_app.config import (
    MODEL_CHOICES,
    get_app_paths,
    is_transformer_model,
    is_ensemble_model,
    is_new_embedding_model,
    resolve_model_selection,
    is_sentence_transformer_model,
    is_cross_encoder_model,
)
from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer
from duplicate_question_app.embedding_models import (
    predict_with_sentence_transformer,
    get_ensemble_prediction,
    get_sentence_transformer_model,
)
from duplicate_question_app.week2_inference import Week2InferenceService, check_week2_artifacts
from duplicate_question_app.week2_inference import is_week2_model  # single source of truth
from duplicate_question_app.agreement_engine import get_agreement_report
from duplicate_question_app.intelligent_ensemble import get_adaptive_ensemble_prediction
from duplicate_question_app.explainability import generate_decision_trace
from duplicate_question_app.error_analyzer import categorize_error, classify_hardness
from duplicate_question_app.confidence_calibration import calibrate_model_prediction, get_model_calibration_params
from duplicate_question_app.model_registry import build_registry, find_registry_entry
from duplicate_question_app.artifacts import (
    build_dataset_summary,
    build_transformer_metrics,
    build_week4_metrics,
    load_dataset_frame,
    load_transformer_predictions,
    load_week2_model_comparison,
    load_week2_vs_week3_comparison,
    load_week4_ablation,
    load_week4_predictions,
    load_week4_threshold_analysis,
    reconstruct_week3_test_frame,
    available_week4_plots,
)
from duplicate_question_app.visuals import (
    create_batch_summary_figure,
    create_confusion_matrix_figure,
    create_pipeline_figure,
    create_probability_figure,
    create_roc_curve_figure,
)

__all__ = [
    "safe_metric", "metric_card_row", "render_footer", "format_model_comparison_for_display",
    "build_model_comparison_table", "get_runtime_context", "get_dataset", "get_dataset_summary",
    "MODEL_CHOICES",
]
