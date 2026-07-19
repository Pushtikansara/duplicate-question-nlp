"""Page modules for the DQD Streamlit application.

Each page is a self-contained module that receives shared dependencies
via its render function parameters. This keeps app.py lightweight and
allows individual page files to stay under 400 lines.
"""

from __future__ import annotations

from duplicate_question_app.agreement_engine import get_agreement_report  # noqa: F401
from duplicate_question_app.artifacts import (  # noqa: F401
    available_week4_plots,
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
)
from duplicate_question_app.confidence_calibration import (  # noqa: F401
    calibrate_model_prediction,
    get_model_calibration_params,
)
from duplicate_question_app.config import (  # noqa: F401
    MODEL_CHOICES,
    get_app_paths,
    is_cross_encoder_model,
    is_ensemble_model,
    is_new_embedding_model,
    is_sentence_transformer_model,
    is_transformer_model,
    resolve_model_selection,
)
from duplicate_question_app.embedding_models import (  # noqa: F401
    get_ensemble_prediction,
    get_sentence_transformer_model,
    predict_with_sentence_transformer,
)
from duplicate_question_app.error_analyzer import categorize_error, classify_hardness  # noqa: F401
from duplicate_question_app.explainability import generate_decision_trace  # noqa: F401
from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer  # noqa: F401
from duplicate_question_app.intelligent_ensemble import get_adaptive_ensemble_prediction  # noqa: F401
from duplicate_question_app.model_registry import build_registry, find_registry_entry  # noqa: F401
from duplicate_question_app.visuals import (  # noqa: F401
    create_batch_summary_figure,
    create_confusion_matrix_figure,
    create_pipeline_figure,
    create_probability_figure,
    create_roc_curve_figure,
)
from duplicate_question_app.week2_inference import (  # noqa: F401
    Week2InferenceService,
    check_week2_artifacts,
    is_week2_model,
)

__all__ = [
    "safe_metric",
    "metric_card_row",
    "render_footer",
    "format_model_comparison_for_display",
    "build_model_comparison_table",
    "get_runtime_context",
    "get_dataset",
    "get_dataset_summary",
    "MODEL_CHOICES",
]
