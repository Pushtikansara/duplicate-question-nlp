from __future__ import annotations

import json
import time
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app.artifacts import (
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
from duplicate_question_app.config import (
    MODEL_CHOICES,
    MODEL_VERSION_SHORT,
    get_app_paths,
    is_transformer_model,
    is_sentence_transformer_model,
    is_cross_encoder_model,
    is_ensemble_model,
    is_new_embedding_model,
    resolve_model_selection,
)
from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer
from duplicate_question_app.embedding_models import (
    predict_with_sentence_transformer,
    predict_batch_sentence_transformer,
    get_ensemble_prediction,
    get_sentence_transformer_model,
)
from duplicate_question_app.week2_inference import Week2InferenceService, is_week2_model, check_week2_artifacts
from duplicate_question_app.agreement_engine import get_agreement_report, agreement_to_dict
from duplicate_question_app.intelligent_ensemble import get_adaptive_ensemble_prediction, compute_adaptive_weights
from duplicate_question_app.explainability import generate_decision_trace
from duplicate_question_app.error_analyzer import categorize_error, classify_hardness
from duplicate_question_app.confidence_calibration import calibrate_model_prediction, get_model_calibration_params
from duplicate_question_app.model_registry import build_registry, get_registry_dict, find_registry_entry
from duplicate_question_app.visuals import (
    create_batch_summary_figure,
    create_confusion_matrix_figure,
    create_pipeline_figure,
    create_probability_figure,
    create_roc_curve_figure,
)

from duplicate_question_app.entity_detector import analyze_entity_mismatch, get_entity_penalty
from duplicate_question_app.intent_detector import get_intent_details, intent_mismatch_penalty
from duplicate_question_app.negation_detector import get_negation_penalty
from duplicate_question_app.contradiction_detector import get_contradiction_penalty
from duplicate_question_app.lexical_penalty import get_lexical_penalty
from duplicate_question_app.adaptive_ensemble_v2 import adaptive_ensemble_predict, compute_ensemble_features, compute_dynamic_weights, clear_caches, get_cache_stats
from duplicate_question_app.confidence_calibration_v2 import (
    CalibrationMethod, evaluate_calibration, calibrate_predictions,
    select_best_calibration, get_calibration_curve_data, save_calibration_params, load_calibration_params
)
from duplicate_question_app.error_logger import (
    ErrorLogger, ErrorLogConfig, ErrorCategory, ErrorExample,
    load_error_log, analyze_error_log, mine_hard_examples, generate_error_report, get_error_logger, log_prediction_error
)
from duplicate_question_app.agreement_dashboard import (
    analyze_model_agreement, compute_model_leaderboard, generate_agreement_summary,
    AgreementDashboard, ModelLeaderboard
)
from duplicate_question_app.explainer import (
    generate_explanation, generate_counterfactual_explanation, generate_feature_importance,
    ExplanationLevel, ExplanationResult
)
from duplicate_question_app.performance_optimizer import (
    InferenceOptimizer, EmbeddingCache, PreprocessingCache, ModelLoader,
    BatchProcessor, get_embedding_cache, get_preprocessing_cache, get_model_loader,
    cached_normalize, clear_all_caches, warmup_caches, benchmark_inference
)
from duplicate_question_app.evaluation import (
    evaluate_model, find_hard_examples, generate_evaluation_report,
    compare_models, generate_model_comparison_plots, EvaluationMetrics, HardExample
)
from duplicate_question_app.hard_test_generator import (
    generate_hard_dataset, save_dataset, load_dataset, print_dataset_stats,
    Category, DifficultyType, HardPair
)

st.set_page_config(
    page_title="Duplicate Question Detection",
    page_icon="NLP",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Global cache for loaded models ---
_model_cache: dict[str, Any] = {}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1200px;}
        .stApp header {background: transparent !important;}
        .hero-card {
            padding: 1.5rem 1.8rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(37,99,235,0.10), rgba(14,165,233,0.06));
            border: 1px solid rgba(37,99,235,0.15);
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .dashboard-card {
            padding: 1.2rem 1.4rem;
            border-radius: 16px;
            border: 1px solid rgba(148,163,184,0.2);
            background: rgba(255,255,255,0.5);
            margin-bottom: 0.8rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            transition: box-shadow 0.2s ease;
        }
        .dashboard-card:hover {box-shadow: 0 4px 12px rgba(0,0,0,0.06);}
        .metric-value {font-size: 1.8rem; font-weight: 700; color: #1E293B;}
        .metric-label {font-size: 0.8rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;}
        .small-note {color: #64748B; font-size: 0.88rem;}
        .section-header {font-size: 1.1rem; font-weight: 600; color: #0F172A; margin: 1.2rem 0 0.6rem 0;}
        .status-badge {display: inline-block; padding: 0.15rem 0.6rem; border-radius: 12px; font-size: 0.78rem; font-weight: 500;}
        .status-ready {background: #DCFCE7; color: #166534;}
        .status-missing {background: #FEE2E2; color: #991B1B;}
        .status-download {background: #DBEAFE; color: #1E40AF;}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
PATHS = get_app_paths(PROJECT_ROOT)


def path_signature(path: Path) -> str:
    if not path.exists():
        return f"{path.name}:missing"
    stat = path.stat()
    return f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}"


@st.cache_data(show_spinner=False)
def _get_dataset(dataset_signature: str) -> pd.DataFrame:
    del dataset_signature
    return load_dataset_frame(PATHS)


def get_dataset() -> pd.DataFrame:
    dataset_path = PATHS.data_dir / "cleaned_quora.parquet"
    if not dataset_path.exists():
        dataset_path = PATHS.data_dir / "cleaned_quora.csv"
    return _get_dataset(path_signature(dataset_path))


@st.cache_data(show_spinner=False)
def _get_dataset_summary(dataset_signature: str) -> dict[str, Any]:
    del dataset_signature
    return build_dataset_summary(get_dataset())


def get_dataset_summary() -> dict[str, Any]:
    dataset_path = PATHS.data_dir / "cleaned_quora.parquet"
    if not dataset_path.exists():
        dataset_path = PATHS.data_dir / "cleaned_quora.csv"
    return _get_dataset_summary(path_signature(dataset_path))


@st.cache_data(show_spinner=False)
def _get_week3_predictions(predictions_signature: str) -> pd.DataFrame:
    del predictions_signature
    return load_transformer_predictions(PATHS)


def get_week3_predictions() -> pd.DataFrame:
    predictions_path = PATHS.transformer_results_dir / "transformer_test_predictions.csv"
    return _get_week3_predictions(path_signature(predictions_path))


@st.cache_data(show_spinner=False)
def _get_week3_test_frame(dataset_signature: str) -> pd.DataFrame:
    del dataset_signature
    return reconstruct_week3_test_frame(PATHS)


def get_week3_test_frame() -> pd.DataFrame:
    dataset_path = PATHS.data_dir / "cleaned_quora.parquet"
    if not dataset_path.exists():
        dataset_path = PATHS.data_dir / "cleaned_quora.csv"
    return _get_week3_test_frame(path_signature(dataset_path))


@st.cache_data(show_spinner=False)
def _get_week3_analysis_frame(dataset_signature: str, predictions_signature: str) -> pd.DataFrame:
    del dataset_signature, predictions_signature
    predictions = get_week3_predictions()
    test_df = get_week3_test_frame()
    if predictions.empty:
        return pd.DataFrame()
    usable_rows = min(len(predictions), len(test_df))
    merged = pd.concat(
        [
            test_df.iloc[:usable_rows].reset_index(drop=True),
            predictions.iloc[:usable_rows].reset_index(drop=True),
        ],
        axis=1,
    )
    merged["error_type"] = "Correct"
    merged.loc[(merged["true_label"] == 0) & (merged["predicted_label"] == 1), "error_type"] = "False Positive"
    merged.loc[(merged["true_label"] == 1) & (merged["predicted_label"] == 0), "error_type"] = "False Negative"
    return merged


def get_week3_analysis_frame() -> pd.DataFrame:
    dataset_path = PATHS.data_dir / "cleaned_quora.parquet"
    if not dataset_path.exists():
        dataset_path = PATHS.data_dir / "cleaned_quora.csv"
    predictions_path = PATHS.transformer_results_dir / "transformer_test_predictions.csv"
    return _get_week3_analysis_frame(path_signature(dataset_path), path_signature(predictions_path))


@st.cache_data(show_spinner=False)
def _get_transformer_metrics(predictions_signature: str) -> dict[str, Any]:
    del predictions_signature
    return build_transformer_metrics(get_week3_predictions())


def get_transformer_metrics() -> dict[str, Any]:
    predictions_path = PATHS.transformer_results_dir / "transformer_test_predictions.csv"
    return _get_transformer_metrics(path_signature(predictions_path))


@st.cache_data(show_spinner=False)
def _get_week4_metrics(predictions_signature: str) -> dict[str, Any]:
    del predictions_signature
    return build_week4_metrics(get_week4_predictions_df())


def get_week4_metrics() -> dict[str, Any]:
    predictions_path = PATHS.week4_results_dir / "predictions_week4.csv"
    return _get_week4_metrics(path_signature(predictions_path))


@st.cache_data(show_spinner=False)
def _get_week2_vs_week3(comparison_signature: str) -> pd.DataFrame:
    del comparison_signature
    return load_week2_vs_week3_comparison(PATHS)


def get_week2_vs_week3() -> pd.DataFrame:
    comparison_path = PATHS.transformer_results_dir / "week2_vs_week3_comparison.csv"
    return _get_week2_vs_week3(path_signature(comparison_path))


@st.cache_data(show_spinner=False)
def _get_week2_model_comparison(comparison_signature: str) -> pd.DataFrame:
    del comparison_signature
    return load_week2_model_comparison(PATHS)


def get_week2_model_comparison() -> pd.DataFrame:
    comparison_path = PATHS.baseline_results_dir / "week2_model_comparison.parquet"
    return _get_week2_model_comparison(path_signature(comparison_path))


@st.cache_data(show_spinner=False)
def _get_week4_ablation_df(ablation_signature: str) -> pd.DataFrame:
    del ablation_signature
    return load_week4_ablation(PATHS)


def get_week4_ablation_df() -> pd.DataFrame:
    ablation_path = PATHS.week4_results_dir / "ablation_study.csv"
    return _get_week4_ablation_df(path_signature(ablation_path))


@st.cache_data(show_spinner=False)
def _get_week4_threshold_df(threshold_signature: str) -> pd.DataFrame:
    del threshold_signature
    return load_week4_threshold_analysis(PATHS)


def get_week4_threshold_df() -> pd.DataFrame:
    threshold_path = PATHS.week4_results_dir / "threshold_analysis.csv"
    return _get_week4_threshold_df(path_signature(threshold_path))


@st.cache_data(show_spinner=False)
def _get_week4_predictions_df(predictions_signature: str) -> pd.DataFrame:
    del predictions_signature
    return load_week4_predictions(PATHS)


def get_week4_predictions_df() -> pd.DataFrame:
    predictions_path = PATHS.week4_results_dir / "predictions_week4.csv"
    return _get_week4_predictions_df(path_signature(predictions_path))


@st.cache_data(show_spinner=False)
def _get_week4_plot_paths(plot_signatures: tuple[str, ...]) -> list[Path]:
    del plot_signatures
    return available_week4_plots(PATHS)


def get_week4_plot_paths() -> list[Path]:
    plot_signatures = tuple(
        path_signature(PATHS.week4_results_dir / filename)
        for filename in ("fig1_threshold_tuning.png", "fig2_error_analysis.png", "fig3_ablation_comparison.png", "fig4_roc_comparison.png")
    )
    return _get_week4_plot_paths(plot_signatures)


def get_inference_service(_cache_key: str = "default") -> tuple[Any, Any]:
    """Load the inference service based on the selected model.
    Uses manual caching via the global _model_cache dict."""
    selected = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    # Check manual cache
    cache_lookup_key = _cache_key if _cache_key != "default" else selected
    if cache_lookup_key in _model_cache:
        return _model_cache[cache_lookup_key]

    # Handle Week 2 models
    if is_week2_model(selected):
        service = Week2InferenceService(PATHS)
        metadata = {
            "model_label": selected,
            "model_version": "week2",
            "decision_threshold": 0.5,
            "threshold_source": "Default 0.50 threshold for classical ML model",
            "device": "cpu",
            "fallback_reason": None,
            "load_errors": (),
            "model_name": selected,
        }
        return service, metadata

    # Handle Ensemble model
    if is_ensemble_model(selected):
        return None, {"model_label": "Semantic Ensemble", "model_version": "ensemble", "device": "cpu"}

    # Handle sentence transformer / cross-encoder models
    if is_new_embedding_model(selected):
        metadata = {
            "model_label": selected,
            "model_version": "phase2",
            "decision_threshold": 0.5,
            "threshold_source": "Default 0.50 threshold",
            "device": "cpu",
            "fallback_reason": None,
            "load_errors": (),
            "model_name": selected,
        }
        return None, metadata

    # Handle transformer models (Week 3 and Week 4)
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version=selected)
    except (ValueError, FileNotFoundError):
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS)
    service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    _model_cache[cache_lookup_key] = (service, metadata)
    return service, metadata


def get_transformer_service(selected: str) -> tuple[DuplicateQuestionInferenceService, Any]:
    """Helper to get a transformer service for a specific model."""
    try:
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS, model_version=selected)
    except (ValueError, FileNotFoundError):
        model, tokenizer, metadata = load_model_and_tokenizer(PATHS)
    service = DuplicateQuestionInferenceService(model=model, tokenizer=tokenizer, metadata=metadata)
    return service, metadata


def load_model_config(model_dir: Path) -> dict[str, Any]:
    config_path = model_dir / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_model_resolution():
    return resolve_model_selection(PATHS)


def get_runtime_context() -> tuple[Any, Any, Any]:
    resolution = get_model_resolution()
    selected = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    cache_key = f"{resolution.cache_key}|model:{selected}"
    service, metadata = get_inference_service(cache_key)
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        threshold = metadata.get("decision_threshold", 0.5)
        st.info(f"Active model: **{model_label}** | Threshold: **{threshold:.2f}** | Device: **CPU**")
    elif hasattr(metadata, "model_label"):
        model_label = metadata.model_label
        threshold = getattr(metadata, "decision_threshold", 0.5)
        device = getattr(metadata, "device", "cpu")
        if metadata.model_version == "week4":
            st.success(f"Active model: **{model_label}** | Threshold: **{threshold}** | Device: **{device}**")
        else:
            st.info(f"Active model: **{model_label}** | Threshold: **{threshold}** | Device: **{device}**")
        if hasattr(metadata, "load_errors") and metadata.load_errors:
            st.info("Earlier load attempts: " + " | ".join(metadata.load_errors))


def build_model_status_table(resolution: Any) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for status in (resolution.week4, resolution.week3):
        rows.append({
            "Model": status.label,
            "Directory": str(status.model_dir.relative_to(PROJECT_ROOT)),
            "Ready": "Yes" if status.ready else "No",
            "Config": "Yes" if status.has_config else "No",
            "Weights": status.weight_file.name if status.weight_file else "Missing",
            "Tokenizer": ", ".join(status.tokenizer_files) if status.tokenizer_files else "Missing",
            "Issues": ", ".join(status.issues) if status.issues else "None",
        })
    # Add Week 2 model info
    week2_artifacts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_artifacts.values())
    week2_issues = []
    if not week2_artifacts["tfidf"]:
        week2_issues.append("TF-IDF vectorizer missing")
    if not week2_artifacts["logistic_regression"]:
        week2_issues.append("Logistic Regression missing")
    if not week2_artifacts["linear_svm"]:
        week2_issues.append("Linear SVM missing")
    rows.append({
        "Model": "Week 2 Models (TF-IDF + LR/SVM)",
        "Directory": "models/week2_models/",
        "Ready": "Yes" if week2_ready else "No",
        "Config": "N/A",
        "Weights": "joblib files" if week2_ready else "Missing",
        "Tokenizer": "N/A",
        "Issues": ", ".join(week2_issues) if week2_issues else "None",
    })
    # Add new model info
    for m_name, m_dir in [
        ("BGE-base-en-v1.5", PATHS.bge_model_dir),
        ("E5-base-v2", PATHS.e5_model_dir),
        ("MPNet-base-v2", PATHS.mpnet_model_dir),
        ("DeBERTa-v3 Cross-Encoder", PATHS.deberta_model_dir),
        ("Cross-Encoder-Quora (Trained)", PATHS.finetuned_cross_encoder_dir),
    ]:
        exists = m_dir.exists() and (m_dir / "config.json").exists()
        rows.append({
            "Model": m_name,
            "Directory": str(m_dir.relative_to(PROJECT_ROOT)) if m_dir.exists() else str(m_dir),
            "Ready": "Yes (via HuggingFace)" if not exists else "Yes (local)",
            "Config": "N/A (HF)",
            "Weights": "N/A (HF)",
            "Tokenizer": "N/A (HF)",
            "Issues": "Will download from HuggingFace on first use" if not exists else "None",
        })
    return pd.DataFrame(rows)


def safe_metric(value: Any, percent: bool = True, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.{decimals}%}"
    return f"{float(value):.{decimals}f}"


def _format_optional_metric(value: Any, percent: bool = True) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.2%}"
    return f"{float(value):.2f}"


def _directory_size_mb(path: Path) -> float | None:
    if not path.exists():
        return None
    total_bytes = sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
    return total_bytes / (1024 * 1024) if total_bytes else None


def _format_model_size(path: Path | None) -> str:
    if path is None:
        return "N/A"
    size_mb = _directory_size_mb(path)
    if size_mb is None:
        return "N/A"
    if size_mb >= 1024:
        return f"{size_mb / 1024:.2f} GB"
    return f"{size_mb:.1f} MB"


def build_model_comparison_table() -> pd.DataFrame:
    week2_df = get_week2_model_comparison()
    week2_vs_week3_df = get_week2_vs_week3()
    week4_ablation_df = get_week4_ablation_df()
    rows: list[dict[str, Any]] = []

    week2_descriptions = {
        "LR + TF-IDF": "Classical baseline using TF-IDF n-grams with Logistic Regression.",
        "SVM + TF-IDF": "Classical baseline using TF-IDF n-grams with Linear SVM.",
    }
    week2_labels = {
        "LR + TF-IDF": "TF-IDF + Logistic Regression (Week 2)",
        "SVM + TF-IDF": "TF-IDF + Linear SVM (Week 2)",
    }
    for source_name in ("LR + TF-IDF", "SVM + TF-IDF"):
        if not week2_df.empty and "Model" in week2_df.columns:
            match = week2_df[week2_df["Model"] == source_name]
        else:
            match = pd.DataFrame()
        row = match.iloc[0].to_dict() if not match.empty else {}
        rows.append({
            "Model": week2_labels[source_name],
            "Accuracy": row.get("Accuracy"),
            "Precision": row.get("Precision (Dup)"),
            "Recall": row.get("Recall (Dup)"),
            "F1 Score": row.get("F1 (Dup)"),
            "ROC AUC": None,
            "Training Time": "N/A",
            "Model Size": "N/A",
            "Short Description": week2_descriptions[source_name],
        })

    week3_row: dict[str, Any] = {}
    if not week2_vs_week3_df.empty and "Method" in week2_vs_week3_df.columns:
        week3_match = week2_vs_week3_df[week2_vs_week3_df["Method"].str.contains("DistilBERT", case=False, na=False)]
        if not week3_match.empty:
            week3_row = week3_match.iloc[0].to_dict()

    week4_row: dict[str, Any] = {}
    if not week4_ablation_df.empty and "Configuration" in week4_ablation_df.columns:
        week4_match = week4_ablation_df[week4_ablation_df["Configuration"].str.contains("Week 4", case=False, na=False)]
        if not week4_match.empty:
            week4_row = week4_match.iloc[-1].to_dict()

    rows.append({
        "Model": "DistilBERT (Week 3)",
        "Accuracy": week3_row.get("Accuracy"),
        "Precision": week3_row.get("Precision"),
        "Recall": week3_row.get("Recall"),
        "F1 Score": week3_row.get("F1 Score"),
        "ROC AUC": None,
        "Training Time": "N/A",
        "Model Size": _format_model_size(PATHS.week3_model_dir),
        "Short Description": "Fine-tuned DistilBERT sequence classifier used as the transformer baseline.",
    })
    rows.append({
        "Model": "Improved DistilBERT (Week 4)",
        "Accuracy": week4_row.get("Accuracy"),
        "Precision": week4_row.get("Precision"),
        "Recall": week4_row.get("Recall"),
        "F1 Score": week4_row.get("F1 Score"),
        "ROC AUC": week4_row.get("ROC-AUC"),
        "Training Time": "N/A",
        "Model Size": _format_model_size(PATHS.week4_model_dir),
        "Short Description": "Week 4 DistilBERT variant with class weighting, tuned threshold, and error-analysis artifacts.",
    })

    # Phase 2 models (placeholder metrics)
    phase2_models = [
        ("BGE-base-en-v1.5", "BGE embedding model for semantic similarity."),
        ("E5-base-v2", "E5 embedding model with contrastive learning."),
        ("MPNet-base-v2", "MPNet masked and permuted language modeling."),
        ("DeBERTa-v3 Cross-Encoder", "Cross-encoder with disentangled attention."),
        ("Semantic Ensemble", "Averaged predictions from all models."),
    ]
    for name, desc in phase2_models:
        rows.append({
            "Model": name,
            "Accuracy": None,
            "Precision": None,
            "Recall": None,
            "F1 Score": None,
            "ROC AUC": None,
            "Training Time": "N/A",
            "Model Size": "Varies",
            "Short Description": desc,
        })

    comparison_df = pd.DataFrame(rows)
    numeric_columns = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]
    for column in numeric_columns:
        comparison_df[column] = pd.to_numeric(comparison_df[column], errors="coerce")
    return comparison_df


def format_model_comparison_for_display(comparison_df: pd.DataFrame) -> pd.DataFrame:
    display_df = comparison_df.copy()
    for column in ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]:
        display_df[column] = display_df[column].map(lambda value: _format_optional_metric(value))
    return display_df


def render_footer() -> None:
    st.markdown("---")
    st.caption("Production-grade Streamlit application for Duplicate Question Detection with 9 models.")


def metric_card_row(metrics: dict[str, Any]) -> None:
    accuracy = metrics.get("accuracy")
    precision = metrics.get("precision")
    recall = metrics.get("recall")
    f1 = metrics.get("f1")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Accuracy", safe_metric(accuracy))
    col2.metric("Precision", safe_metric(precision))
    col3.metric("Recall", safe_metric(recall))
    col4.metric("F1 Score", safe_metric(f1))


def get_model_metrics_for(model_name: str) -> dict[str, Any]:
    if model_name == "TF-IDF + Logistic Regression (Week 2)":
        df = get_week2_model_comparison()
        if not df.empty and "Model" in df.columns:
            row = df[df["Model"] == "LR + TF-IDF"]
            if not row.empty:
                r = row.iloc[0]
                return {"accuracy": r.get("Accuracy"), "precision": r.get("Precision (Dup)"), "recall": r.get("Recall (Dup)"), "f1": r.get("F1 (Dup)"), "roc_auc": None}
    elif model_name == "TF-IDF + Linear SVM (Week 2)":
        df = get_week2_model_comparison()
        if not df.empty and "Model" in df.columns:
            row = df[df["Model"] == "SVM + TF-IDF"]
            if not row.empty:
                r = row.iloc[0]
                return {"accuracy": r.get("Accuracy"), "precision": r.get("Precision (Dup)"), "recall": r.get("Recall (Dup)"), "f1": r.get("F1 (Dup)"), "roc_auc": None}
    elif model_name == "DistilBERT (Week 3)":
        return get_transformer_metrics()
    elif model_name == "Improved DistilBERT (Week 4)":
        return get_week4_metrics()
    return {}


def render_home_page() -> None:
    """Professional dashboard homepage."""
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        _, metadata, resolution = get_runtime_context()
    except Exception:
        resolution = get_model_resolution()
        metadata = None

    try:
        summary = get_dataset_summary()
    except Exception:
        summary = {"rows": 0, "duplicate_ratio": 0.0}

    week2_arts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_arts.values())
    active_metrics = get_model_metrics_for(selected_model)

    registry = build_registry(PATHS)
    loaded_count = sum(1 for e in registry if e.load_status == "loaded" or e.load_status == "available")
    total_models = len(registry)

    # Active model info
    if is_transformer_model(selected_model) and metadata and not isinstance(metadata, dict):
        model_desc = metadata.model_label
        model_device = metadata.device
        model_threshold = metadata.decision_threshold
    elif is_week2_model(selected_model):
        model_desc = selected_model
        model_device = "cpu"
        model_threshold = 0.5
    else:
        model_desc = selected_model
        model_device = "cpu"
        model_threshold = 0.5

    # Hero section
    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin:0 0 0.15rem 0; font-size:1.6rem;">Duplicate Question Detection</h1>
            <p style="margin:0 0 0.4rem 0; color:#475569; font-size:0.95rem;">
                Research-grade semantic duplicate detection with {total_models} models
            </p>
            <p class="small-note">
                Active: <strong>{model_desc}</strong> · {model_device.upper()} · threshold {model_threshold:.2f}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dashboard metric cards
    st.markdown("<div class='section-header'>System Overview</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Model", model_desc[:28] + "..." if len(model_desc) > 28 else model_desc)
    col2.metric("Available Models", f"{loaded_count}/{total_models}")
    col3.metric("Inference Device", model_device.upper())
    col4.metric("Dataset Size", f"{summary['rows']:,} pairs")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duplicate Ratio", safe_metric(summary.get("duplicate_ratio", 0)))
    col2.metric("Week 2 (LR/SVM)", "✅ Ready" if week2_ready else "❌ Missing")
    col3.metric("Week 3 (DistilBERT)", "✅" if resolution.week3.ready else "❌")
    col4.metric("Week 4 (Improved)", "✅" if resolution.week4.ready else "❌")

    # Active model performance
    if active_metrics and any(v is not None for v in [active_metrics.get("accuracy"), active_metrics.get("f1")]):
        st.markdown("<div class='section-header'>Active Model Performance</div>", unsafe_allow_html=True)
        metric_card_row(active_metrics)

    # Model status overview
    st.markdown("<div class='section-header'>Model Registry</div>", unsafe_allow_html=True)
    reg_data = []
    for e in registry:
        status_icon = "✅" if e.has_artifacts or e.source == "built-in" else ("⬇️" if e.source == "huggingface" else "❌")
        reg_data.append({
            "Model": e.display_name,
            "Type": e.model_type.replace("-", " ").title(),
            "Framework": e.framework.upper(),
            "Source": e.source.title(),
            "Status": status_icon,
            "Params": e.parameters,
        })
    reg_df = pd.DataFrame(reg_data)
    st.dataframe(reg_df, use_container_width=True, hide_index=True,
                 column_config={"Status": st.column_config.TextColumn("Status", width="small")})


def render_project_overview_page() -> None:
    st.title("Project Overview")
    st.write("This project identifies whether two questions express the same intent. The workflow evolved from data cleaning and classical NLP baselines to transformer fine-tuning and advanced embedding models.")

    overview_col1, overview_col2 = st.columns([1.2, 1])
    with overview_col1:
        st.subheader("Week-by-Week Progress")
        st.markdown("""
        - **Week 1:** Data collection, cleaning, exploratory data analysis, and preprocessing
        - **Week 2:** TF-IDF, Word2Vec, Sentence-BERT features, and classical ML baselines
        - **Week 3:** DistilBERT fine-tuning with a reusable inference pipeline
        - **Week 4:** Threshold tuning, class imbalance handling, and error analysis
        - **Week 5:** Streamlit application, dashboarding, deployment assets
        - **Phase 2:** BGE, E5, MPNet, DeBERTa, and Semantic Ensemble
        """)
    with overview_col2:
        st.subheader("Current App Behavior")
        st.markdown("""
        - Loads **Week 4 improved model** when its Hugging Face artifacts are present
        - Falls back to **Week 3 DistilBERT** automatically
        - **Week 2 models** loaded from joblib files
        - **Phase 2 models** loaded from HuggingFace/sentence-transformers
        - **Semantic Ensemble** averages predictions from all available models
        """)


def render_dataset_page() -> None:
    st.title("Dataset Information")
    try:
        df = get_dataset()
        summary = get_dataset_summary()
    except Exception as exc:
        st.error(f"Dataset could not be loaded: {exc}")
        return
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{summary['rows']:,}")
    col2.metric("Duplicate", f"{summary['label_counts'].get(1, 0):,}")
    col3.metric("Non-Duplicate", f"{summary['label_counts'].get(0, 0):,}")
    col4.metric("Columns", len(summary["columns"]))
    tab_summary, tab_quality, tab_preview = st.tabs(["Summary", "Data Quality", "Preview"])
    with tab_summary:
        st.subheader("Columns")
        st.write(summary["columns"])
        label_counts = pd.Series(summary["label_counts"]).rename(index={0: "Non-Duplicate", 1: "Duplicate"})
        if not label_counts.empty:
            st.subheader("Class Distribution")
            st.bar_chart(label_counts)
    with tab_quality:
        st.subheader("Missing Values")
        missing_df = pd.DataFrame.from_dict(summary["missing_values"], orient="index", columns=["missing_count"]).sort_values("missing_count", ascending=False)
        st.dataframe(missing_df, use_container_width=True)
    with tab_preview:
        st.subheader("Sample Records")
        st.dataframe(summary["preview"], use_container_width=True)
        if {"clean_q1", "clean_q2"}.issubset(df.columns):
            st.subheader("Cleaned Text Samples")
            st.dataframe(df[["clean_q1", "clean_q2"]].head(10), use_container_width=True)


def render_pipeline_page() -> None:
    st.title("NLP Pipeline Visualization")
    st.write("This visualization shows how the project evolved from raw data to a deployed prediction interface.")
    pipeline_figure = create_pipeline_figure()
    st.pyplot(pipeline_figure, clear_figure=True)
    with st.expander("Pipeline Details", expanded=True):
        st.markdown("""- **Input layer:** two user questions
- **Tokenizer:** DistilBERT pair tokenization with max_length=128
- **Classifier:** fine-tuned sequence classification head
- **Post-processing:** probability computation, thresholding, confidence scoring
- **Phase 2:** Additional embedding models and ensemble""")


def render_model_information_page() -> None:
    st.title("Model Information")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        resolution = get_model_resolution()
    except Exception as exc:
        st.error(f"Model info could not be loaded: {exc}")
        return

    if is_week2_model(selected_model):
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", selected_model)
        col2.metric("Decision Threshold", "0.50")
        col3.metric("Model Type", "Classical ML (TF-IDF + Linear Model)")
        st.dataframe(pd.DataFrame([{"Model Type": "TF-IDF + Logistic Regression / Linear SVM", "Feature Extraction": "TF-IDF with ngram_range=(1,2), max_features=5000", "Training Data": "Full Quora dataset (404,290 pairs)", "Label": "is_duplicate (binary)"}]), use_container_width=True, hide_index=True)
    elif is_new_embedding_model(selected_model):
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", selected_model)
        col2.metric("Decision Threshold", "0.50")
        col3.metric("Model Type", "Embedding / Cross-Encoder")
        st.info(f"{selected_model} is loaded via HuggingFace / sentence-transformers. It runs on CPU.")
    else:
        try:
            _, metadata, _ = get_runtime_context()
        except Exception:
            metadata = None
        if metadata and not isinstance(metadata, dict):
            model_config = load_model_config(metadata.model_dir)
            col1, col2, col3 = st.columns(3)
            col1.metric("Active Model", metadata.model_label)
            col2.metric("Decision Threshold", f"{metadata.decision_threshold:.2f}")
            col3.metric("Threshold Source", metadata.threshold_source)
            render_model_runtime_message(metadata)
            if model_config:
                st.subheader("Architecture Summary")
                config_subset = {"Architecture": ", ".join(model_config.get("architectures") or []), "Model Type": model_config.get("model_type"), "Number of Labels": model_config.get("num_labels"), "Vocabulary Size": model_config.get("vocab_size"), "Hidden Size": model_config.get("dim", model_config.get("hidden_size"))}
                st.dataframe(pd.DataFrame([config_subset]), use_container_width=True, hide_index=True)
        else:
            st.info(f"Model info for {selected_model} is not yet available.")

    st.subheader("Artifact Readiness")
    st.dataframe(build_model_status_table(resolution), use_container_width=True, hide_index=True)


def render_prediction_page() -> None:
    st.title("Prediction Page")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
        device = metadata.get("device", "cpu")
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
        device = metadata.device
    else:
        model_label = selected_model
        decision_threshold = 0.5
        device = "cpu"

    st.caption(f"Running live inference with **{model_label}** on **{device}**. Decision threshold: **{decision_threshold:.2f}**.")

    with st.form("single_prediction_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=120)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=120)
        submitted = st.form_submit_button("Predict Duplicate Status", use_container_width=True)

    if submitted:
        if not question1.strip() or not question2.strip():
            st.error("Both question fields are required.")
            return

        with st.spinner(f"Running inference with {model_label}..."):
            try:
                start_time = time.time()
                if is_week2_model(selected_model):
                    result = service.predict_single(question1, question2, selected_model)
                elif is_ensemble_model(selected_model):
                    result = get_ensemble_prediction(question1, question2)
                elif is_new_embedding_model(selected_model):
                    result = predict_with_sentence_transformer(selected_model, question1, question2)
                else:
                    result = service.predict_single(question1, question2)
                result["inference_time"] = time.time() - start_time
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", result["prediction"])
        col2.metric("Confidence", f"{result['confidence']:.2%}")
        col3.metric("Probability (Duplicate)", f"{result['prob_duplicate']:.2%}")
        col4.metric("Threshold", f"{result['threshold']:.2f}")

        st.caption(f"Model: **{result['model_label']}** | ⏱️ Inference time: {result['inference_time']*1000:.1f} ms")

        if result.get("reason"):
            st.info(f"ℹ️ {result['reason']}")

        if result.get("feature_breakdown"):
            with st.expander("Model Contributions (Ensemble)"):
                for model_name, contrib in result["feature_breakdown"].items():
                    st.write(f"- **{model_name}**: duplicate probability = {contrib.get('prob_dup', 0):.4f}")

        st.success(f"Model decision: **{result['prediction']}** using **{result['model_label']}**.")
        probability_figure = create_probability_figure(prob_duplicate=float(result["prob_duplicate"]), threshold=float(result["threshold"]))
        st.pyplot(probability_figure, clear_figure=True)


def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    candidate_pairs = [("q1", "q2"), ("question1", "question2"), ("sentence1", "sentence2")]
    for col1, col2 in candidate_pairs:
        if col1 in df.columns and col2 in df.columns:
            return col1, col2
    return None


def render_batch_prediction_page() -> None:
    st.title("Batch CSV Prediction")
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")

    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
        decision_threshold = metadata.get("decision_threshold", 0.5)
    elif metadata:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
    else:
        model_label = selected_model
        decision_threshold = 0.5

    st.caption(f"Batch inference uses **{model_label}** with threshold **{decision_threshold:.2f}**.")

    template_df = pd.DataFrame({"q1": ["How do I learn Python?", "What is the capital of France?"], "q2": ["How can I learn Python programming?", "Which city is the largest in France?"]})
    st.download_button("Download CSV Template", data=template_df.to_csv(index=False).encode("utf-8"), file_name="duplicate_question_template.csv", mime="text/csv")

    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is None:
        st.info("Upload a CSV file with `q1/q2`, `question1/question2`, or `sentence1/sentence2` columns.")
        return

    try:
        batch_df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to read the uploaded CSV: {exc}")
        return

    column_pair = _detect_question_columns(batch_df)
    if column_pair is None:
        st.error("Could not find valid question columns in the uploaded CSV.")
        return

    question1_column, question2_column = column_pair
    prepared_df = batch_df.copy()
    prepared_df[question1_column] = prepared_df[question1_column].fillna("").astype(str).str.strip()
    prepared_df[question2_column] = prepared_df[question2_column].fillna("").astype(str).str.strip()
    valid_mask = prepared_df[question1_column].ne("") & prepared_df[question2_column].ne("")

    col1, col2, col3 = st.columns(3)
    col1.metric("Uploaded Rows", f"{len(batch_df):,}")
    col2.metric("Valid Rows", f"{int(valid_mask.sum()):,}")
    col3.metric("Skipped Rows", f"{int((~valid_mask).sum()):,}")

    if (~valid_mask).any():
        st.warning("Rows with empty question text will be skipped.")
    st.subheader("Preview")
    st.dataframe(batch_df.head(10), use_container_width=True)

    if st.button("Run Batch Prediction", use_container_width=True):
        if not valid_mask.any():
            st.error("No valid rows found.")
            return
        try:
            question_pairs = list(zip(prepared_df.loc[valid_mask, question1_column], prepared_df.loc[valid_mask, question2_column]))
            with st.spinner(f"Processing {len(question_pairs)} pairs with {model_label}..."):
                if is_week2_model(selected_model):
                    valid_results_df = service.predict_batch(question_pairs, selected_model)
                else:
                    if is_ensemble_model(selected_model):
                        results_list = []
                        for q1, q2 in question_pairs:
                            r = get_ensemble_prediction(q1, q2)
                            results_list.append(r)
                        valid_results_df = pd.DataFrame(results_list)
                    elif is_new_embedding_model(selected_model):
                        valid_results_df = pd.DataFrame(
                            predict_batch_sentence_transformer(selected_model, question_pairs, batch_size=64)
                        )
                    else:
                        results_list = []
                        for q1, q2 in question_pairs:
                            r = service.predict_single(q1, q2)
                            results_list.append(r)
                        valid_results_df = pd.DataFrame(results_list)
        except Exception as exc:
            st.error(f"Batch prediction failed: {exc}")
            return

        merged_results = batch_df.copy()
        merged_results["batch_status"] = "Skipped: empty question text"
        valid_index = prepared_df.index[valid_mask]
        merged_results.loc[valid_index, "batch_status"] = "Predicted"
        for column in valid_results_df.columns:
            merged_results[column] = pd.NA
            merged_results.loc[valid_index, column] = valid_results_df[column].to_numpy() if hasattr(valid_results_df[column], "to_numpy") else valid_results_df[column].values

        st.success(f"Generated predictions for {len(merged_results):,} question pairs.")
        st.dataframe(merged_results, use_container_width=True)
        summary_figure = create_batch_summary_figure(merged_results[merged_results["batch_status"] == "Predicted"])
        st.pyplot(summary_figure, clear_figure=True)
        st.download_button("Download Prediction Results", data=merged_results.to_csv(index=False).encode("utf-8"), file_name="duplicate_question_predictions.csv", mime="text/csv")


def render_model_comparison_page() -> None:
    st.title("Model Comparison")
    st.write("Side-by-side comparison across all models: Week 2 classical baselines, Week 3/4 transformers, and Phase 2 embedding models.")

    comparison_df = build_model_comparison_table()
    display_df = format_model_comparison_for_display(comparison_df)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    metric_columns = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]
    chart_df = comparison_df.set_index("Model")[metric_columns].dropna(axis=1, how="all")
    if not chart_df.empty:
        st.subheader("Metric Comparison")
        st.bar_chart(chart_df)

    week4_row = comparison_df[comparison_df["Model"] == "Improved DistilBERT (Week 4)"]
    week3_row = comparison_df[comparison_df["Model"] == "DistilBERT (Week 3)"]
    if not week4_row.empty and not week3_row.empty:
        wk4_f1 = week4_row.iloc[0]["F1 Score"]
        wk3_f1 = week3_row.iloc[0]["F1 Score"]
        wk4_acc = week4_row.iloc[0]["Accuracy"]
        wk3_acc = week3_row.iloc[0]["Accuracy"]
        col1, col2 = st.columns(2)
        if not pd.isna(wk4_f1) and not pd.isna(wk3_f1):
            col1.metric("Week 4 F1", safe_metric(wk4_f1), delta=f"{wk4_f1 - wk3_f1:+.2%}")
        if not pd.isna(wk4_acc) and not pd.isna(wk3_acc):
            col2.metric("Week 4 Accuracy", safe_metric(wk4_acc), delta=f"{wk4_acc - wk3_acc:+.2%}")

    st.subheader("Model Details")
    detail_data = {
        "Model": comparison_df["Model"].tolist(),
        "Type": ["Classical ML", "Classical ML", "Transformer", "Transformer", "Bi-Encoder", "Bi-Encoder", "Bi-Encoder", "Cross-Encoder", "Ensemble"],
        "Parameters": ["~10K features", "~10K features", "66.9M", "66.9M", "110M", "118M", "110M", "184M", "Varies"],
    }
    st.dataframe(pd.DataFrame(detail_data), use_container_width=True, hide_index=True)


def render_dashboard_page() -> None:
    st.title("Performance Dashboard")
    week3_metrics = get_transformer_metrics()
    week4_metrics = get_week4_metrics()

    tab_week4, tab_week3, tab_compare = st.tabs(["Week 4 (Improved)", "Week 3 (Baseline)", "Comparison"])

    with tab_week4:
        if not week4_metrics:
            st.info("Week 4 prediction artifacts are not available.")
        else:
            metric_card_row(week4_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(create_confusion_matrix_figure(week4_metrics["confusion_matrix"]), clear_figure=True)
            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week4_metrics.get("roc_curve")
                roc_auc = week4_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(create_roc_curve_figure(roc_curve_data["fpr"], roc_curve_data["tpr"], roc_auc), clear_figure=True)
                else:
                    st.info("ROC data is not available.")
            threshold_df = get_week4_threshold_df()
            if not threshold_df.empty and {"Threshold", "F1"}.issubset(threshold_df.columns):
                best_f1 = float(threshold_df["F1"].max())
                best_threshold = float(threshold_df.loc[threshold_df["F1"] == best_f1, "Threshold"].astype(float).max())
                col1, col2 = st.columns(2)
                col1.metric("Best Threshold", f"{best_threshold:.2f}")
                col2.metric("Best F1 (tuning)", f"{best_f1:.3f}")
                with st.expander("Threshold Tuning Table"):
                    st.dataframe(threshold_df, use_container_width=True)
            week4_ablation = get_week4_ablation_df()
            if not week4_ablation.empty:
                with st.expander("Ablation Study", expanded=True):
                    st.dataframe(week4_ablation, use_container_width=True)

    with tab_week3:
        if not week3_metrics:
            st.warning("Week 3 prediction artifacts are missing.")
        else:
            metric_card_row(week3_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(create_confusion_matrix_figure(week3_metrics["confusion_matrix"]), clear_figure=True)
            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week3_metrics.get("roc_curve")
                roc_auc = week3_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(create_roc_curve_figure(roc_curve_data["fpr"], roc_curve_data["tpr"], roc_auc), clear_figure=True)
                else:
                    st.info("ROC data is not available.")
            comparison_df = get_week2_vs_week3()
            st.subheader("Week 2 vs Week 3 Comparison")
            if not comparison_df.empty:
                st.dataframe(comparison_df, use_container_width=True)
                if "Method" in comparison_df.columns:
                    chart_cols = [col for col in ["Accuracy", "Precision", "Recall", "F1 Score"] if col in comparison_df.columns]
                    if chart_cols:
                        st.bar_chart(comparison_df.set_index("Method")[chart_cols])
            else:
                st.info("Week 2 vs Week 3 comparison not available.")

    with tab_compare:
        comparison_df = build_model_comparison_table()
        st.dataframe(format_model_comparison_for_display(comparison_df), use_container_width=True, hide_index=True)
        chart_df = comparison_df.set_index("Model")[["Accuracy", "Precision", "Recall", "F1 Score"]].dropna(axis=1, how="all")
        if not chart_df.empty:
            st.bar_chart(chart_df)


def render_error_analysis_page() -> None:
    st.title("Error Analysis")
    week4_df = get_week4_predictions_df()
    week3_df = get_week3_analysis_frame()

    tabs = []
    if not week4_df.empty:
        tabs.append("Week 4")
    tabs.append("Week 3")
    tab_objects = st.tabs(tabs)

    def render_error_frame(title: str, df: pd.DataFrame, label_columns: tuple[str, str]) -> None:
        label_true, label_pred = label_columns
        working = df.copy()
        if "error_type" not in working.columns and {label_true, label_pred}.issubset(working.columns):
            working["error_type"] = "Correct"
            working.loc[(working[label_true] == 0) & (working[label_pred] == 1), "error_type"] = "False Positive"
            working.loc[(working[label_true] == 1) & (working[label_pred] == 0), "error_type"] = "False Negative"
        if "error_type" in working.columns:
            normalized_error = working["error_type"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
            normalized_error = normalized_error.mask(normalized_error.str.contains("False Positive", na=False), "False Positive")
            normalized_error = normalized_error.mask(normalized_error.str.contains("False Negative", na=False), "False Negative")
            normalized_error = normalized_error.mask(normalized_error.str.contains("Correct", na=False), "Correct")
            working["error_type"] = normalized_error
        if "confidence" not in working.columns and {"prob_duplicate", "prob_non_duplicate"}.issubset(working.columns):
            working["confidence"] = working[["prob_duplicate", "prob_non_duplicate"]].max(axis=1)
        if title == "Week 4":
            if "q1" not in working.columns and "question1" in working.columns:
                working["q1"] = working["question1"]
            if "q2" not in working.columns and "question2" in working.columns:
                working["q2"] = working["question2"]
            if "actual_class_name" not in working.columns and label_true in working.columns:
                working["actual_class_name"] = working[label_true].map({0: "Non-Duplicate", 1: "Duplicate"})
            if "predicted_class_name" not in working.columns and label_pred in working.columns:
                working["predicted_class_name"] = working[label_pred].map({0: "Non-Duplicate", 1: "Duplicate"})
        if working.empty or "error_type" not in working.columns:
            st.warning("Prediction artifacts are required for error analysis.")
            return
        error_df = working[working["error_type"] != "Correct"].copy()
        fp_df = working[working["error_type"] == "False Positive"].copy()
        fn_df = working[working["error_type"] == "False Negative"].copy()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Errors", f"{len(error_df):,}")
        col2.metric("False Positives", f"{len(fp_df):,}")
        col3.metric("False Negatives", f"{len(fn_df):,}")
        st.bar_chart(working["error_type"].value_counts())
        if not error_df.empty and "confidence" in error_df.columns:
            st.subheader("Most Confident Errors")
            display_cols = [col for col in ["q1", "q2", "actual_class_name", "predicted_class_name", "confidence", "prob_duplicate", "error_type"] if col in error_df.columns]
            top_errors = error_df.nlargest(min(10, len(error_df)), "confidence")[display_cols]
            st.dataframe(top_errors, use_container_width=True)
        tab1, tab2 = st.tabs(["False Positives", "False Negatives"])
        with tab1:
            cols = [col for col in ["q1", "q2", "prob_duplicate", "confidence"] if col in fp_df.columns]
            st.dataframe(fp_df[cols].head(10), use_container_width=True)
        with tab2:
            cols = [col for col in ["q1", "q2", "prob_duplicate", "confidence"] if col in fn_df.columns]
            st.dataframe(fn_df[cols].head(10), use_container_width=True)

    tab_index = 0
    if not week4_df.empty:
        with tab_objects[tab_index]:
            render_error_frame("Week 4", week4_df, ("true_label", "pred_label"))
        tab_index += 1
    with tab_objects[tab_index]:
        render_error_frame("Week 3", week3_df, ("true_label", "predicted_label"))


def render_explainability_page() -> None:
    st.title("Explainability and Results")
    week4_plots = get_week4_plot_paths()
    week4_threshold_df = get_week4_threshold_df()
    week4_ablation = get_week4_ablation_df()
    week4_predictions = get_week4_predictions_df()
    week4_metrics = get_week4_metrics()

    if not week4_plots and week4_threshold_df.empty and week4_ablation.empty and week4_predictions.empty:
        st.info("Week 4 exported artifacts are not fully available yet.")
        return

    tab_overview, tab_threshold, tab_ablation, tab_predictions, tab_visuals = st.tabs(["Overview", "Threshold Tuning", "Ablation", "Predictions", "Visuals"])
    with tab_overview:
        if week4_metrics:
            metric_card_row(week4_metrics)
        st.write("Week 4 focuses on threshold tuning, handling class imbalance, and deeper error analysis.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Plots Found", len(week4_plots))
        col2.metric("Threshold Rows", f"{len(week4_threshold_df):,}")
        col3.metric("Prediction Rows", f"{len(week4_predictions):,}")
    with tab_threshold:
        if week4_threshold_df.empty:
            st.info("Threshold analysis is not available.")
        else:
            if {"Threshold", "F1"}.issubset(week4_threshold_df.columns):
                best_f1 = float(week4_threshold_df["F1"].max())
                best_threshold = float(week4_threshold_df.loc[week4_threshold_df["F1"] == best_f1, "Threshold"].astype(float).max())
                col1, col2 = st.columns(2)
                col1.metric("Selected Threshold", f"{best_threshold:.2f}")
                col2.metric("Best F1", f"{best_f1:.3f}")
            st.dataframe(week4_threshold_df, use_container_width=True)
    with tab_ablation:
        if week4_ablation.empty:
            st.info("Ablation study table is not available.")
        else:
            st.dataframe(week4_ablation, use_container_width=True)
    with tab_predictions:
        if week4_predictions.empty:
            st.info("Week 4 prediction export is not available.")
        else:
            st.dataframe(week4_predictions.head(25), use_container_width=True)
    with tab_visuals:
        if not week4_plots:
            st.info("No exported Week 4 visuals were found.")
        else:
            for plot_path in week4_plots:
                st.image(str(plot_path), caption=plot_path.name, use_container_width=True)


def render_model_agreement_page() -> None:
    """Research-grade Model Agreement & Decision Trace page."""
    st.title("Model Agreement & Decision Trace")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Analyze how all 9 models agree/disagree, view adaptive weights, "
        "lexical features, semantic features, and a full decision trace.</p>",
        unsafe_allow_html=True,
    )

    with st.form("agreement_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=80)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=80)
        submitted = st.form_submit_button("Analyze Agreement", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Collecting predictions from all 9 models..."):
            try:
                trace = generate_decision_trace(q1, q2, PATHS)
                td = trace.to_dict()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        # Final Decision
        decision = td["decision"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Prediction", decision["final_prediction"])
        col2.metric("Probability", f"{decision['final_probability']:.2%}")
        col3.metric("Confidence", f"{decision['confidence']:.2%}")
        col4.metric("Ensemble Method", decision["ensemble_method"])

        # Model Agreement
        agreement = td["model_agreement"]
        st.subheader("🤝 Model Agreement")
        agree_col, disagree_col, score_col, unan_col = st.columns(4)
        agree_col.metric("Models Agreeing", len(agreement["models_agreeing"]))
        disagree_col.metric("Models Disagreeing", len(agreement["models_disagreeing"]))
        score_col.metric("Agreement Score", f"{agreement['agreement_score']:.0%}")
        unan_col.metric("Unanimous", "✅ Yes" if agreement["is_unanimous"] else "❌ No")

        tab_models, tab_lexical, tab_semantic, tab_weights, tab_scores = st.tabs([
            "Per-Model Scores", "Lexical Features", "Semantic Features",
            "Adaptive Weights", "Per-Model Similarities",
        ])

        with tab_models:
            scores = td["per_model_scores"]
            rows = []
            for name, prob in scores.items():
                if prob is not None:
                    rows.append({"Model": name.replace("_", " ").title(), "Probability": prob})
            if rows:
                st.dataframe(pd.DataFrame(rows).sort_values("Probability", ascending=False),
                           use_container_width=True, hide_index=True)
            st.info("💡 Models with probability > 0.5 vote 'Duplicate', < 0.5 vote 'Non-Duplicate'.")

        with tab_lexical:
            lex = td["lexical_features"]
            cols = st.columns(4)
            cols[0].metric("Word Overlap", f"{lex['word_overlap']:.1%}")
            cols[1].metric("Char Overlap", f"{lex['char_overlap']:.1%}")
            cols[2].metric("Word Count Diff", lex["word_count_diff"])
            cols[3].metric("Char Count Diff", lex["char_count_diff"])
            if lex["word_overlap"] < 0.2:
                st.warning("⚠️ Low lexical overlap — semantic understanding is essential for this pair.")
            elif lex["word_overlap"] > 0.6:
                st.success("✅ High lexical overlap — lexical models (TF-IDF) are well-suited here.")

        with tab_semantic:
            sem = td["semantic_features"]
            cols = st.columns(3)
            cols[0].metric("Abbreviations", sem["abbreviation_count"])
            cols[1].metric("Synonyms", len(sem["synonyms"]))
            cols[2].metric("Semantic Depth", f"{td['semantic_depth']:.2f}")
            if sem["abbreviations"]:
                st.info(f"📝 Abbreviations detected: {', '.join(sem['abbreviations'])}")
            if sem["named_entities_q1"] or sem["named_entities_q2"]:
                st.caption(f"Named entities — Q1: {sem['named_entities_q1'][:3]}, Q2: {sem['named_entities_q2'][:3]}")

        with tab_weights:
            w = td["adaptive_weights"]
            if w:
                weight_df = pd.DataFrame([
                    ("Lexical (TF-IDF)", w.get("lexical", 0)),
                    ("Transformer (DistilBERT)", w.get("transformer", 0)),
                    ("Embedding (BGE/E5/MPNet)", w.get("embedding", 0)),
                    ("Cross-Encoder (DeBERTa)", w.get("cross_encoder", 0)),
                ], columns=["Model Group", "Weight"])
                st.bar_chart(weight_df.set_index("Model Group"))
                st.dataframe(weight_df, use_container_width=True, hide_index=True)
                st.info("💡 Weights adapt based on lexical overlap, abbreviation presence, and synonym detection.")

        with tab_scores:
            sims = td["per_model_scores"]
            sim_data = {}
            for k, v in sims.items():
                if "similarity" in k or "score" in k:
                    sim_data[k.replace("_", " ").title()] = v
            if any(v is not None for v in sim_data.values()):
                st.dataframe(
                    pd.DataFrame([(k, f"{v:.4f}") for k, v in sim_data.items() if v is not None],
                                 columns=["Metric", "Value"]),
                    use_container_width=True, hide_index=True,
                )


def render_calibration_page() -> None:
    """Confidence Calibration analysis page."""
    st.title("Confidence Calibration")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Calibrates model confidences using temperature scaling, Platt scaling, "
        "and isotonic regression. Shows calibration curves and ECE metrics.</p>",
        unsafe_allow_html=True,
    )

    st.subheader("Model Calibration Parameters")
    params_data = []
    for model_name in MODEL_CHOICES:
        if model_name == "Semantic Ensemble":
            continue
        cp = get_model_calibration_params(model_name)
        params_data.append({
            "Model": model_name,
            "Method": cp["method"].title(),
            "Temperature": cp["temperature"],
        })
    st.dataframe(pd.DataFrame(params_data), use_container_width=True, hide_index=True)

    st.subheader("Interactive Calibration Demo")
    with st.form("calibration_form"):
        model = st.selectbox("Select a model", [m for m in MODEL_CHOICES if m != "Semantic Ensemble"])
        raw_prob = st.slider("Raw probability", 0.0, 1.0, 0.7, 0.05)
        cal_submitted = st.form_submit_button("Calibrate", use_container_width=True)

    if cal_submitted:
        cp = get_model_calibration_params(model)
        calibrated = calibrate_model_prediction(model, raw_prob)
        delta = calibrated - raw_prob
        col1, col2, col3 = st.columns(3)
        col1.metric("Raw Probability", f"{raw_prob:.2%}")
        col2.metric("Calibrated Probability", f"{calibrated:.2%}", delta=f"{delta:+.2%}")
        col3.metric("Method", cp["method"].title())
        st.caption(f"Temperature: {cp['temperature']:.1f}")


def render_hard_examples_page() -> None:
    """Hard Negative Mining page."""
    st.title("Hard Example Mining")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Test specific question pairs to see error categorization and hardness classification.</p>",
        unsafe_allow_html=True,
    )

    with st.form("hard_example_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=80)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=80)
        has_ground_truth = st.checkbox("I know the ground truth label")
        true_label = None
        if has_ground_truth:
            true_label = st.selectbox("Ground truth", ["Non-Duplicate", "Duplicate"])
            true_label = 0 if true_label == "Non-Duplicate" else 1
        submitted = st.form_submit_button("Analyze", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing..."):
            try:
                report = get_agreement_report(q1, q2, PATHS)
                errors = categorize_error(q1, q2, report.predicted_label, true_label, report.prob_mean)
                hardness = classify_hardness(report.prob_mean, report.confidence_mean,
                                            report.agreement_score, report.predicted_label, true_label)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", report.prediction)
        col2.metric("Hardness", hardness.upper())
        col3.metric("Agreement", f"{report.agreement_score:.0%}")
        col4.metric("Models Voting", report.num_models_voted)

        st.subheader("Error Categories")
        for err in errors:
            if err.detected:
                status = "⚠️" if err.name != "No Error Detected" else "✅"
                st.markdown(f"{status} **{err.name}** — {err.description}")
                if err.details:
                    st.caption(f"   Details: {err.details}")

        st.subheader("Model Votes")
        vote_data = [{"Model": v.model_name, "Prob": f"{v.prob_duplicate:.4f}",
                      "Vote": "Duplicate" if v.predicted_label == 1 else "Non-Duplicate"}
                     for v in report.votes if v.error is None]
        st.dataframe(pd.DataFrame(vote_data), use_container_width=True, hide_index=True)


def render_model_manager_page() -> None:
    """Model Manager — complete registry view with status for all models."""
    st.title("Model Manager")
    st.markdown("<p style='color:#64748B;font-size:0.95rem;'>Complete model registry — inspect all 9 models, their metadata, status, and configuration.</p>", unsafe_allow_html=True)

    registry = build_registry(PATHS)
    resolution = get_model_resolution()

    st.markdown("<div class='section-header'>All Models</div>", unsafe_allow_html=True)
    rows = []
    for e in registry:
        rows.append({
            "Model": e.display_name,
            "Type": e.model_type.replace("-", " ").title(),
            "Framework": e.framework.upper(),
            "Source": e.source.title(),
            "Device": e.device.upper(),
            "Size": f"{e.size_mb:.0f} MB" if e.size_mb else "N/A",
            "Params": e.parameters,
            "Status": "✅ Ready" if e.has_artifacts or e.source == "built-in" else "⚠️ Auto-download" if e.source == "huggingface" else "❌ Missing",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Model Details</div>", unsafe_allow_html=True)
    selected = st.selectbox("Select a model for details", [e.display_name for e in registry], key="model_mgr_select")
    entry = find_registry_entry(selected, PATHS)
    if entry:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**Display Name:** {entry.display_name}")
            st.markdown(f"**Internal ID:** `{entry.internal_id}`")
            st.markdown(f"**Type:** {entry.model_type}")
            st.markdown(f"**Framework:** {entry.framework}")
            st.markdown(f"**Source:** {entry.source}")
            st.markdown(f"**Version:** {entry.version}")
            st.markdown(f"**Device:** {entry.device}")
        with col2:
            st.markdown(f"**Parameters:** {entry.parameters}")
            st.markdown(f"**Embedding Size:** {entry.embedding_size or 'N/A'}")
            st.markdown(f"**Hidden Size:** {entry.hidden_size or 'N/A'}")
            st.markdown(f"**Local Path:** `{entry.local_path or 'N/A'}`")
            st.markdown(f"**Cache Path:** `{entry.cache_path or 'N/A'}`")
            st.markdown(f"**Status:** {entry.load_status}")
        st.markdown(f"**Description:** {entry.description}")
        if entry.advantages:
            st.markdown(f"**Advantages:** {'; '.join(entry.advantages)}")
        if entry.weaknesses:
            st.markdown(f"**Weaknesses:** {'; '.join(entry.weaknesses)}")
        st.markdown(f"**Recommended Use:** {entry.recommended_use}")

    st.markdown("---")
    st.markdown("<div class='section-header'>Model Artifact Paths</div>", unsafe_allow_html=True)
    path_rows = []
    for e in registry:
        path_rows.append({
            "Model": e.display_name,
            "Local Path": e.local_path or "—",
            "Cache Path": e.cache_path or "—",
        })
    st.dataframe(pd.DataFrame(path_rows), use_container_width=True, hide_index=True)

# ============================================================
# PHASE 3 PAGES
# ============================================================

def render_entity_analysis_page() -> None:
    """Entity Detection Analysis page."""
    st.title("Entity Detection Analysis")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Extract and compare entities (programming languages, frameworks, OS, companies, etc.) "
        "between two questions. Entity mismatches apply penalties to duplicate probability.</p>",
        unsafe_allow_html=True,
    )

    with st.form("entity_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Entities", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Extracting entities..."):
            try:
                result = analyze_entity_mismatch(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Entity Penalty", f"{result.mismatch_penalty:.2%}")
        col2.metric("Q1 Entities", len(result.q1_entities))
        col3.metric("Q2 Entities", len(result.q2_entities))
        col4.metric("Overlap Types", len(result.entity_overlap))

        # Details
        tab1, tab2, tab3 = st.tabs(["Q1 Entities", "Q2 Entities", "Mismatches"])

        with tab1:
            if result.q1_entities:
                df = pd.DataFrame([{"Type": e.entity_type, "Value": e.value, "Confidence": f"{e.confidence:.0%}"} for e in result.q1_entities])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No entities detected in Question 1")

        with tab2:
            if result.q2_entities:
                df = pd.DataFrame([{"Type": e.entity_type, "Value": e.value, "Confidence": f"{e.confidence:.0%}"} for e in result.q2_entities])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No entities detected in Question 2")

        with tab3:
            if result.entity_mismatch:
                for etype, (q1_only, q2_only) in result.entity_mismatch.items():
                    if q1_only or q2_only:
                        st.write(f"**{etype}**: Q1={sorted(q1_only) if q1_only else '—'} | Q2={sorted(q2_only) if q2_only else '—'}")
            if result.penalty_details:
                st.subheader("Penalty Details")
                for detail in result.penalty_details:
                    st.caption(detail)


def render_intent_analysis_page() -> None:
    """Intent Detection Analysis page."""
    st.title("Question Intent Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Classify question intent (Definition, Comparison, Installation, Tutorial, Troubleshooting, etc.). "
        "Mismatched intents reduce duplicate probability.</p>",
        unsafe_allow_html=True,
    )

    with st.form("intent_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Intent", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting intent..."):
            try:
                details = get_intent_details(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3 = st.columns(3)
        col1.metric("Intent Penalty", f"{details['mismatch_penalty']:.2%}")
        col2.metric("Q1 Intent", details['q1_intent'].replace('_', ' ').title())
        col3.metric("Q2 Intent", details['q2_intent'].replace('_', ' ').title())

        st.caption(f"Compatible: {'✅ Yes' if details['compatible'] else '❌ No'}")
        st.caption(f"Reason: {details['mismatch_reason']}")

        with st.expander("Details"):
            st.json({
                "q1_scores": details['q1_all_scores'],
                "q2_scores": details['q2_all_scores'],
                "q1_patterns": details['q1_patterns'],
                "q2_patterns": details['q2_patterns'],
            })


def render_negation_analysis_page() -> None:
    """Negation Detection Analysis page."""
    st.title("Negation Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Detect negation words (not, never, without, remove, disable, uninstall, delete, stop, prevent) "
        "that flip question meaning. Negation mismatches apply strong penalties.</p>",
        unsafe_allow_html=True,
    )

    with st.form("negation_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Negation", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting negation..."):
            try:
                penalty, details = get_negation_penalty(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2 = st.columns(2)
        col1.metric("Negation Penalty", f"{penalty:.2%}")
        col2.metric("Details", details)

        # Show detected negations
        from duplicate_question_app.negation_detector import detect_negations
        q1_negs = detect_negations(q1)
        q2_negs = detect_negations(q2)

        tab1, tab2 = st.tabs(["Q1 Negations", "Q2 Negations"])
        with tab1:
            if q1_negs:
                df = pd.DataFrame([{"Text": n.text, "Type": n.negation_type, "Scope": n.scope.value, "Confidence": f"{n.confidence:.0%}", "Target": n.target or "—"} for n in q1_negs])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No negations detected in Question 1")

        with tab2:
            if q2_negs:
                df = pd.DataFrame([{"Text": n.text, "Type": n.negation_type, "Scope": n.scope.value, "Confidence": f"{n.confidence:.0%}", "Target": n.target or "—"} for n in q2_negs])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No negations detected in Question 2")


def render_contradiction_analysis_page() -> None:
    """Contradiction Detection Analysis page."""
    st.title("Contradiction Detection")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Detect contradictory meaning between questions using pattern matching and NLI models. "
        "Contradictions strongly indicate non-duplicate.</p>",
        unsafe_allow_html=True,
    )

    with st.form("contradiction_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Detect Contradiction", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Detecting contradictions..."):
            try:
                from duplicate_question_app.contradiction_detector import detect_contradiction
                result = detect_contradiction(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2, col3 = st.columns(3)
        col1.metric("Has Contradiction", "✅ Yes" if result.has_contradiction else "❌ No")
        col2.metric("Contradiction Score", f"{result.contradiction_score:.2%}")
        col3.metric("Types", len(result.contradiction_types))

        if result.details:
            st.subheader("Contradiction Details")
            for detail in result.details.split("; "):
                st.write(f"• {detail}")

        if result.nli_scores:
            st.subheader("NLI Scores")
            st.json(result.nli_scores)


def render_lexical_analysis_page() -> None:
    """Lexical Penalty Analysis page."""
    st.title("Lexical Penalty Engine")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Analyze lexical mismatches: different nouns, verbs, named entities, software names, "
        "programming languages, and products. Penalties applied when key terms differ.</p>",
        unsafe_allow_html=True,
    )

    with st.form("lexical_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Lexical Mismatch", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing lexical mismatch..."):
            try:
                penalty, details = get_lexical_penalty(q1, q2)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        col1, col2 = st.columns(2)
        col1.metric("Lexical Penalty", f"{penalty:.2%}")
        col2.metric("Details", details)

        # Detailed breakdown
        from duplicate_question_app.lexical_penalty import compute_lexical_penalty, extract_tokens
        result = compute_lexical_penalty(q1, q2)

        tab1, tab2, tab3 = st.tabs(["Q1 Tokens", "Q2 Tokens", "Overlap Scores"])
        with tab1:
            for k, v in result.q1_tokens.items():
                if v:
                    st.write(f"**{k}**: {sorted(v)}")
        with tab2:
            for k, v in result.q2_tokens.items():
                if v:
                    st.write(f"**{k}**: {sorted(v)}")
        with tab3:
            df = pd.DataFrame([{"Type": k, "Overlap": f"{v:.2%}"} for k, v in result.overlap_scores.items()])
            st.dataframe(df, use_container_width=True, hide_index=True)

        if result.penalties:
            st.subheader("Penalties Applied")
            for ptype, pval in result.penalties.items():
                st.write(f"• {ptype.value}: {pval:.2%}")
            for detail in result.details:
                st.caption(detail)


def render_adaptive_ensemble_v2_page() -> None:
    """Adaptive Ensemble V2 Prediction page."""
    st.title("Adaptive Ensemble V2 — Dynamic Confidence Routing")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Next-generation ensemble with dynamic weight routing based on input features. "
        "Weights adapt: high lexical mismatch → boost cross-encoder/TF-IDF; "
        "high semantic agreement → boost transformers.</p>",
        unsafe_allow_html=True,
    )

    with st.form("ensemble_v2_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Run Adaptive Ensemble V2", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Running adaptive ensemble..."):
            try:
                result = adaptive_ensemble_predict(q1, q2, PATHS)
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        # Final decision
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prediction", result["prediction"])
        col2.metric("Probability", f"{result['prob_duplicate']:.2%}")
        col3.metric("Confidence", f"{result['confidence']:.2%}")
        col4.metric("Latency", f"{result['latency_ms']:.1f} ms")

        # Adaptive weights
        st.subheader("Dynamic Weights")
        weights = result["adaptive_weights"]
        weight_df = pd.DataFrame([
            ("TF-IDF", weights.get("tfidf_weight", 0)),
            ("Transformer", weights.get("transformer_weight", 0)),
            ("Embedding", weights.get("embedding_weight", 0)),
            ("Cross-Encoder", weights.get("cross_encoder_weight", 0)),
        ], columns=["Model Group", "Weight"])
        st.bar_chart(weight_df.set_index("Model Group"))
        st.dataframe(weight_df, use_container_width=True, hide_index=True)

        # Feature analysis
        st.subheader("Feature Analysis")
        features = result["features"]
        feat_df = pd.DataFrame([
            ("Lexical Overlap", features.get("lexical_overlap", 0)),
            ("Semantic Depth", features.get("semantic_depth", 0)),
            ("Entity Penalty", features.get("entity_penalty", 0)),
            ("Intent Penalty", features.get("intent_penalty", 0)),
            ("Negation Penalty", features.get("negation_penalty", 0)),
            ("Contradiction Penalty", features.get("contradiction_penalty", 0)),
            ("Lexical Penalty", features.get("lexical_penalty", 0)),
            ("Model Agreement", features.get("model_agreement", 0)),
            ("Prob Std", features.get("prob_std", 0)),
            ("Is Borderline", features.get("is_borderline", False)),
        ], columns=["Feature", "Value"])
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

        # Model contributions
        st.subheader("Model Contributions")
        contrib = result.get("feature_breakdown", {})
        if contrib:
            contrib_df = pd.DataFrame([
                {"Model": k, "Prob": v.get("prob_dup", v.get("prob_duplicate", 0)), "Weight": v.get("weight", 0), "Weighted": v.get("weighted_contribution", 0)}
                for k, v in contrib.items()
            ])
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)

        # Reason
        st.info(f"Reason: {result.get('reason', 'N/A')}")


def render_calibration_v2_page() -> None:
    """Advanced Calibration page with Temperature/Platt/Isotonic."""
    st.title("Advanced Confidence Calibration")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Calibrate model confidences using Temperature Scaling, Platt Scaling, and Isotonic Regression. "
        "Evaluate with ECE, MCE, Brier Score, and calibration curves.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Interactive Demo", "Batch Calibration", "Calibration Curves"])

    with tab1:
        st.subheader("Interactive Calibration Demo")
        with st.form("cal_v2_form"):
            model = st.selectbox("Select model", [m for m in MODEL_CHOICES if m != "Semantic Ensemble"])
            method = st.selectbox("Calibration method", [m.value for m in CalibrationMethod])
            raw_prob = st.slider("Raw probability", 0.0, 1.0, 0.7, 0.01)
            cal_submitted = st.form_submit_button("Calibrate", use_container_width=True)

        if cal_submitted:
            try:
                calibrated = calibrate_model_prediction(model, raw_prob)
                delta = calibrated - raw_prob
                col1, col2, col3 = st.columns(3)
                col1.metric("Raw Probability", f"{raw_prob:.2%}")
                col2.metric("Calibrated", f"{calibrated:.2%}", delta=f"{delta:+.2%}")
                col3.metric("Method", method.title())
            except Exception as exc:
                st.error(f"Calibration failed: {exc}")

    with tab2:
        st.subheader("Batch Calibration from Predictions")
        st.info("Upload a CSV with columns: true_label, prob_duplicate")
        uploaded = st.file_uploader("Upload predictions CSV", type=["csv"])

        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                if 'true_label' in df.columns and 'prob_duplicate' in df.columns:
                    y_true = df['true_label'].values
                    y_prob = df['prob_duplicate'].values

                    results = {}
                    for method in [CalibrationMethod.TEMPERATURE, CalibrationMethod.PLATT, CalibrationMethod.ISOTONIC]:
                        result = calibrate_predictions(y_prob, y_true, method)
                        results[method.value] = {
                            "ece_before": result.metrics_before.ece,
                            "ece_after": result.metrics_after.ece,
                            "brier_before": result.metrics_before.brier_score,
                            "brier_after": result.metrics_after.brier_score,
                            "params": result.parameters,
                        }

                    st.dataframe(pd.DataFrame(results).T, use_container_width=True)

                    # Best method
                    best = min(results.items(), key=lambda x: x[1]["ece_after"])
                    st.success(f"Best method: {best[0]} (ECE: {best[1]['ece_after']:.4f})")
                else:
                    st.error("CSV must contain 'true_label' and 'prob_duplicate' columns")
            except Exception as exc:
                st.error(f"Batch calibration failed: {exc}")

    with tab3:
        st.subheader("Calibration Curve (Reliability Diagram)")
        st.info("Upload predictions to generate calibration curve")

        uploaded = st.file_uploader("Upload for calibration curve", type=["csv"], key="cal_curve")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                if 'true_label' in df.columns and 'prob_duplicate' in df.columns:
                    y_true = df['true_label'].values
                    y_prob = df['prob_duplicate'].values

                    curve_data = get_calibration_curve_data(y_prob, y_true)

                    fig, ax = plt.subplots(figsize=(6, 5))
                    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect')
                    ax.plot(curve_data['bin_centers'], curve_data['bin_accuracies'], 'o-', linewidth=2, markersize=8)
                    ax.set_xlabel('Mean Predicted Probability')
                    ax.set_ylabel('Fraction of Positives')
                    ax.set_title('Calibration Curve')
                    ax.legend()
                    ax.grid(alpha=0.3)
                    st.pyplot(fig, clear_figure=True)
            except Exception as exc:
                st.error(f"Curve generation failed: {exc}")


def render_error_logger_page() -> None:
    """Error Logger & Hard Example Mining page."""
    st.title("Error Logger & Hard Example Mining")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Automatically log prediction errors for analysis. Mine hardest examples for model improvement.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Log Error", "View Error Log", "Hard Example Mining"])

    with tab1:
        st.subheader("Log a Prediction Error")
        with st.form("error_log_form"):
            q1 = st.text_area("Question 1", height=80)
            q2 = st.text_area("Question 2", height=80)
            col1, col2 = st.columns(2)
            with col1:
                pred = st.selectbox("Predicted", ["Non-Duplicate", "Duplicate"])
                pred_label = 0 if pred == "Non-Duplicate" else 1
            with col2:
                true = st.selectbox("True Label", ["Non-Duplicate", "Duplicate"])
                true_label = 0 if true == "Non-Duplicate" else 1

            prob_dup = st.slider("Duplicate Probability", 0.0, 1.0, 0.5, 0.01)
            confidence = st.slider("Confidence", 0.0, 1.0, 0.5, 0.01)
            model_name = st.text_input("Model Name", "Adaptive Ensemble V2")
            notes = st.text_area("Notes (optional)")

            if st.form_submit_button("Log Error", use_container_width=True):
                if pred_label != true_label:
                    logger = get_error_logger()
                    example = logger.log_error(
                        question1=q1, question2=q2, predicted_label=pred_label,
                        true_label=true_label, prob_duplicate=prob_dup,
                        confidence=confidence, model_name=model_name,
                        notes=notes
                    )
                    st.success(f"Error logged: {example.q1[:50]}... vs {example.q2[:50]}...")
                else:
                    st.warning("Prediction matches true label - not an error")

    with tab2:
        st.subheader("Error Log Analysis")
        log_path = st.text_input("Log file path", "hard_examples.csv")

        if st.button("Analyze Log"):
            try:
                df = load_error_log(Path(log_path))
                if df.empty:
                    st.info("No errors logged yet")
                else:
                    analysis = analyze_error_log(df)
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Errors", analysis['total_errors'])
                    col2.metric("False Positives", analysis['false_positives'])
                    col3.metric("False Negatives", analysis['false_negatives'])
                    col4.metric("Avg Confidence", f"{analysis['confidence_stats']['mean']:.2%}")

                    st.subheader("Error Categories")
                    if analysis['error_categories']:
                        cat_df = pd.DataFrame(list(analysis['error_categories'].items()), columns=["Category", "Count"])
                        st.bar_chart(cat_df.set_index("Category"))

                    st.subheader("Top Confident Errors")
                    if analysis['top_confident_errors']:
                        st.dataframe(pd.DataFrame(analysis['top_confident_errors']), use_container_width=True)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    with tab3:
        st.subheader("Mine Hard Examples")
        log_path = st.text_input("Log file path", "hard_examples.csv", key="mine_log")
        strategy = st.selectbox("Mining strategy", ["confidence", "disagreement", "lexical", "balanced"])
        n = st.slider("Number of examples", 10, 500, 50)

        if st.button("Mine Examples"):
            try:
                df = load_error_log(Path(log_path))
                if df.empty:
                    st.info("No data to mine")
                else:
                    hard_df = mine_hard_examples(df, n=n, strategy=strategy)
                    st.dataframe(hard_df, use_container_width=True)

                    # Download
                    csv = hard_df.to_csv(index=False).encode()
                    st.download_button("Download Hard Examples", data=csv, file_name="hard_examples_mined.csv", mime="text/csv")
            except Exception as exc:
                st.error(f"Mining failed: {exc}")


def render_agreement_dashboard_page() -> None:
    """Model Agreement Dashboard page."""
    st.title("Model Agreement Dashboard")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Deep agreement analysis: Agreement %, Confidence spread, Entropy, Variance, "
        "Strongest/Weakest/Most Influential models.</p>",
        unsafe_allow_html=True,
    )

    with st.form("agreement_dash_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        submitted = st.form_submit_button("Analyze Agreement", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Analyzing model agreement..."):
            try:
                dashboard = analyze_model_agreement(q1, q2, PATHS)
                summary = generate_agreement_summary(q1, q2, PATHS)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

        # Overview
        st.subheader("Agreement Summary")
        for key, value in summary.items():
            if key != 'interpretation':
                st.caption(f"{key}: {value}")
        if 'interpretation' in summary:
            st.info(summary['interpretation'])

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Agreement %", f"{dashboard.agreement_percentage:.0%}")
        col2.metric("Confidence Spread", f"{dashboard.confidence_spread:.1%}")
        col3.metric("Prediction Entropy", f"{dashboard.prediction_entropy:.3f}")
        col4.metric("Prob Variance", f"{dashboard.probability_variance:.4f}")

        # Model votes
        st.subheader("Model Votes")
        vote_df = pd.DataFrame(dashboard.model_votes)
        st.dataframe(vote_df, use_container_width=True, hide_index=True)

        # Disagreements
        if dashboard.models_disagreeing:
            st.warning(f"Models disagreeing: {', '.join(dashboard.models_disagreeing)}")
        else:
            st.success("All models agree!")

        # Calibration status
        st.subheader("Calibration Status")
        cal_df = pd.DataFrame(list(dashboard.calibration_status.items()), columns=["Model", "Status"])
        st.dataframe(cal_df, use_container_width=True, hide_index=True)


def render_leaderboard_page() -> None:
    """Model Leaderboard page."""
    st.title("Model Leaderboard")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Rank models by accuracy, confidence, calibration, agreement, influence, and speed.</p>",
        unsafe_allow_html=True,
    )

    st.info("Upload a predictions CSV with columns: true_label, prob_duplicate, and model-specific columns")

    uploaded = st.file_uploader("Upload predictions", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            if 'true_label' in df.columns and 'prob_duplicate' in df.columns:
                leaderboard = compute_model_leaderboard([df.to_dict('records')], df['true_label'].tolist())
                st.subheader("Leaderboard")
                st.dataframe(pd.DataFrame({
                    'Accuracy': leaderboard.by_accuracy,
                    'Confidence': leaderboard.by_confidence,
                    'Calibration (ECE)': leaderboard.by_calibration,
                    'Agreement': leaderboard.by_agreement,
                    'Influence': leaderboard.by_influence,
                    'Speed': leaderboard.by_speed,
                }), use_container_width=True)

                col1, col2, col3 = st.columns(3)
                col1.success(f"🏆 Strongest: {leaderboard.get_strongest_model()}")
                col2.warning(f"⚠️ Weakest: {leaderboard.get_weakest_model()}")
                col3.info(f"🎯 Most Influential: {leaderboard.get_most_influential()}")
            else:
                st.error("CSV must contain 'true_label' and 'prob_duplicate' columns")
        except Exception as exc:
            st.error(f"Leaderboard failed: {exc}")


def render_explainer_page() -> None:
    """Advanced Explainability page with plain English explanations."""
    st.title("Advanced Explainability — Plain English")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate human-readable explanations for any prediction. "
        "See exactly why the model decided Duplicate or Non-Duplicate.</p>",
        unsafe_allow_html=True,
    )

    with st.form("explainer_form"):
        q1 = st.text_area("Question 1", placeholder="Enter the first question", height=100)
        q2 = st.text_area("Question 2", placeholder="Enter the second question", height=100)
        level = st.selectbox("Explanation level", [l.value for l in ExplanationLevel], index=1)
        submitted = st.form_submit_button("Generate Explanation", use_container_width=True)

    if submitted and q1.strip() and q2.strip():
        with st.spinner("Generating explanation..."):
            try:
                # First get prediction
                result = adaptive_ensemble_predict(q1, q2, PATHS)
                explanation = generate_explanation(q1, q2, result, ExplanationLevel(level), PATHS)
            except Exception as exc:
                st.error(f"Explanation failed: {exc}")
                return

        # Display
        st.subheader("Explanation")
        st.text(explanation.to_text())

        # Counterfactual
        st.subheader("Counterfactual Analysis")
        counterfactual = generate_counterfactual_explanation(q1, q2, result, PATHS)
        st.write(f"**Current**: {counterfactual['current_prediction']} ({counterfactual['current_probability']:.1%})")
        st.write(f"**Target**: {counterfactual['target_prediction']}")
        st.write(f"**Difficulty**: {counterfactual['difficulty']}")
        for change in counterfactual['required_changes']:
            st.write(f"• **{change['factor']}**: {change['current']} → {change['action']} (Impact: {change['impact']})")

        # Feature importance
        st.subheader("Feature Importance")
        importance = generate_feature_importance(result)
        if importance:
            imp_df = pd.DataFrame(importance)
            st.dataframe(imp_df, use_container_width=True, hide_index=True)


def render_performance_optimizer_page() -> None:
    """Performance Optimization page."""
    st.title("Performance Optimizer")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Cache embeddings, batch encode, memoize preprocessing. Benchmark inference latency.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Cache Stats", "Benchmark", "Optimization Tips"])

    with tab1:
        st.subheader("Cache Statistics")
        emb_cache = get_embedding_cache()
        prep_cache = get_preprocessing_cache()

        col1, col2 = st.columns(2)
        with col1:
            stats = emb_cache.stats()
            st.metric("Embedding Cache Hits", stats.hits)
            st.metric("Embedding Cache Misses", stats.misses)
            st.metric("Hit Rate", f"{stats.hit_rate:.1%}")
            st.metric("Cache Size", f"{stats.size}/{stats.max_size}")
        with col2:
            stats = prep_cache.stats()
            st.metric("Preprocessing Cache Hits", stats.hits)
            st.metric("Preprocessing Cache Misses", stats.misses)
            st.metric("Hit Rate", f"{stats.hit_rate:.1%}")
            st.metric("Cache Size", f"{stats.size}/{stats.max_size}")

        if st.button("Clear All Caches"):
            clear_all_caches()
            st.success("Caches cleared!")

    with tab2:
        st.subheader("Benchmark Inference")
        model_names = st.multiselect("Models to benchmark", MODEL_CHOICES, default=MODEL_CHOICES[:3])
        n_pairs = st.slider("Number of test pairs", 10, 500, 50)
        iterations = st.slider("Iterations", 1, 10, 3)

        if st.button("Run Benchmark"):
            with st.spinner("Benchmarking..."):
                try:
                    # Generate random pairs for testing
                    test_pairs = [
                        ("How to install Python?", "How to setup Python?"),
                        ("Java vs JavaScript", "Difference between Java and JS"),
                        ("Docker uninstall", "Remove Docker"),
                        ("AWS vs Azure", "Compare AWS and Azure"),
                        ("TensorFlow vs PyTorch", "TF vs PyTorch comparison"),
                    ] * (n_pairs // 5 + 1)
                    test_pairs = test_pairs[:n_pairs]

                    results = benchmark_inference(test_pairs, model_names, iterations)
                    bench_df = pd.DataFrame(results).T
                    st.dataframe(bench_df, use_container_width=True)

                    # Plot
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(bench_df.index, bench_df['per_pair_ms'])
                    ax.set_ylabel('ms per pair')
                    ax.set_title('Inference Latency per Pair')
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig, clear_figure=True)
                except Exception as exc:
                    st.error(f"Benchmark failed: {exc}")

    with tab3:
        st.subheader("Optimization Tips")
        st.markdown("""
        - **Embedding Cache**: Reuses computed embeddings for repeated questions (major speedup for batch)
        - **Preprocessing Cache**: Memoizes text normalization results
        - **Batch Encoding**: Encodes multiple texts in a single forward pass
        - **Model Preloading**: Load all models at startup to avoid cold starts
        - **LRU Eviction**: Prevents unbounded memory growth
        - **Thread Safety**: All caches are thread-safe for concurrent requests
        """)


def render_evaluation_page() -> None:
    """Comprehensive Evaluation page."""
    st.title("Model Evaluation & Comparison")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate Confusion Matrix, ROC, PR Curve, Calibration Curve, "
        "Top 100 hardest failures, per-model comparison, FP/FN reports.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Single Model Evaluation", "Multi-Model Comparison"])

    with tab1:
        st.subheader("Single Model Evaluation")
        uploaded = st.file_uploader("Upload predictions CSV", type=["csv"])
        model_name = st.text_input("Model name", "Adaptive Ensemble V2")
        output_dir = st.text_input("Output directory", "evaluation_results")

        if uploaded and st.button("Generate Report"):
            with st.spinner("Generating evaluation report..."):
                try:
                    df = pd.read_csv(uploaded)
                    summary = generate_evaluation_report(
                        df, Path(output_dir), model_name=model_name
                    )
                    st.success("Report generated!")
                    st.json(summary)

                    # Show plots
                    for name, path in summary['plots'].items():
                        if Path(path).exists():
                            st.image(path, caption=name)
                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")

    with tab2:
        st.subheader("Multi-Model Comparison")
        st.info("Upload multiple CSVs, one per model, with same true_label column")

        uploaded_files = st.file_uploader("Upload model predictions", type=["csv"], accept_multiple_files=True)
        model_names = st.text_input("Model names (comma-separated)", "Model A, Model B, Model C")

        if uploaded_files and st.button("Compare Models"):
            try:
                names = [n.strip() for n in model_names.split(',')]
                predictions_dict = {}
                for name, file in zip(names, uploaded_files):
                    predictions_dict[name] = pd.read_csv(file)

                # Compare
                comparison_df = compare_models(predictions_dict)
                st.dataframe(comparison_df, use_container_width=True)

                # Plots
                output_dir = Path("comparison_plots")
                plot_paths = generate_model_comparison_plots(predictions_dict, output_dir)
                for name, path in plot_paths.items():
                    if Path(path).exists():
                        st.image(path, caption=name)
            except Exception as exc:
                st.error(f"Comparison failed: {exc}")


def render_hard_test_generator_page() -> None:
    """Hard Test Dataset Generator page."""
    st.title("Hard Test Dataset Generator")
    st.markdown(
        "<p style='color: #64748B; font-size: 0.95rem;'>"
        "Generate 1000+ extremely difficult question pairs across 13 categories with "
        "abbreviations, synonyms, negation, paraphrases, entity swaps, and contradictions.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        n_pairs = st.slider("Total pairs", 100, 5000, 1000, 100)
        output_path = st.text_input("Output path", "hard_test_dataset.csv")
    with col2:
        include_duplicates = st.checkbox("Include duplicate pairs (paraphrases)", value=True)
        include_non_duplicates = st.checkbox("Include non-duplicate pairs", value=True)

    if st.button("Generate Dataset"):
        with st.spinner("Generating hard test dataset..."):
            try:
                dataset = generate_hard_dataset(
                    n_pairs=n_pairs,
                    include_duplicates=include_duplicates,
                    include_non_duplicates=include_non_duplicates,
                )
                save_dataset(dataset, Path(output_path))
                st.success(f"Generated {len(dataset)} pairs saved to {output_path}")

                # Show stats
                stats = print_dataset_stats(dataset)
                st.json(stats)

                # Preview
                st.subheader("Preview")
                preview_df = pd.DataFrame([p.to_dict() for p in dataset[:20]])
                st.dataframe(preview_df, use_container_width=True)

                # Download
                csv = pd.DataFrame([p.to_dict() for p in dataset]).to_csv(index=False).encode()
                st.download_button("Download CSV", data=csv, file_name="hard_test_dataset.csv", mime="text/csv")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")

    registry = build_registry(PATHS)


def sidebar_navigation() -> str:
    st.sidebar.title("🔬 DQD System")
    st.sidebar.markdown("<div style='margin:-0.5rem 0 0.5rem 0;color:#64748B;font-size:0.78rem;'>Duplicate Question Detection</div>", unsafe_allow_html=True)

    # Single radio with all pages, grouped by markdown headers
    st.sidebar.markdown("### 📌 Main")
    main_pages = ["⏎ Home", "Prediction Page", "Batch CSV Prediction", "Model Comparison", "Performance Dashboard"]
    st.sidebar.markdown("### 🔬 Research")
    research_pages = ["Research: Model Agreement", "Research: Decision Trace", "Research: Calibration", "Research: Error Explorer"]
    st.sidebar.markdown("### 🧪 Phase 3: False Positive Reduction")
    phase3_pages = [
        "Entity Detection", "Intent Detection", "Negation Detection", "Contradiction Detection",
        "Lexical Penalty", "Adaptive Ensemble V2", "Advanced Calibration", "Error Logger",
        "Agreement Dashboard", "Advanced Explainability", "Performance Optimizer",
        "Evaluation Suite", "Hard Test Generator"
    ]
    st.sidebar.markdown("### 🛠️ Developer")
    dev_pages = ["Model Manager", "Project Overview", "Dataset Information", "Pipeline", "Model Info", "Error Analysis", "Explainability"]

    all_pages = main_pages + research_pages + phase3_pages + dev_pages

    # Remember the last page in session state
    default_page = st.session_state.get("current_page", "⏎ Home")
    default_idx = all_pages.index(default_page) if default_page in all_pages else 0

    selected = st.sidebar.radio("Navigate", all_pages, index=default_idx, key="nav", label_visibility="collapsed")
    st.session_state["current_page"] = selected

    # Model selector
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 Model")
    prev_model = st.session_state.get("selected_model", None)
    model_sel = st.sidebar.selectbox(
        "Select model", MODEL_CHOICES,
        index=MODEL_CHOICES.index(prev_model) if prev_model in MODEL_CHOICES else 3,
        key="selected_model_widget", label_visibility="collapsed",
    )

    if model_sel != prev_model:
        st.session_state["selected_model"] = model_sel
        _model_cache.clear()
        import duplicate_question_app.embedding_models as em
        em._sentence_transformer_cache.clear()
        st.rerun()

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "Improved DistilBERT (Week 4)"

    # Active model status
    resolution = get_model_resolution()
    model_name = st.session_state["selected_model"]
    try:
        _, metadata, _ = get_runtime_context()
        if isinstance(metadata, dict):
            st.sidebar.caption(f"Active: {metadata.get('model_label', model_name)[:30]}")
        elif metadata:
            st.sidebar.caption(f"Active: {metadata.model_label[:30]}")
        else:
            st.sidebar.caption(f"Active: {model_name[:30]}")
    except Exception:
        st.sidebar.caption(f"Active: {model_name[:30]}")

    week2_ready = all(check_week2_artifacts(PATHS).values())
    st.sidebar.caption(f"W2: {'✅' if week2_ready else '❌'}  W3: {'✅' if resolution.week3.ready else '❌'}  W4: {'✅' if resolution.week4.ready else '❌'}")

    page_map = {
        "⏎ Home": "Landing Page",
        "Prediction Page": "Prediction Page",
        "Batch CSV Prediction": "Batch CSV Prediction",
        "Model Comparison": "Model Comparison",
        "Performance Dashboard": "Performance Dashboard",
        "Research: Model Agreement": "Research: Model Agreement",
        "Research: Decision Trace": "Research: Decision Trace",
        "Research: Calibration": "Research: Calibration",
        "Research: Error Explorer": "Research: Error Explorer",
        "Entity Detection": "Entity Detection",
        "Intent Detection": "Intent Detection",
        "Negation Detection": "Negation Detection",
        "Contradiction Detection": "Contradiction Detection",
        "Lexical Penalty": "Lexical Penalty",
        "Adaptive Ensemble V2": "Adaptive Ensemble V2",
        "Advanced Calibration": "Advanced Calibration",
        "Error Logger": "Error Logger",
        "Agreement Dashboard": "Agreement Dashboard",
        "Advanced Explainability": "Advanced Explainability",
        "Performance Optimizer": "Performance Optimizer",
        "Evaluation Suite": "Evaluation Suite",
        "Hard Test Generator": "Hard Test Generator",
        "Model Manager": "Model Manager",
        "Project Overview": "Project Overview",
        "Dataset Information": "Dataset Information",
        "Pipeline": "NLP Pipeline Visualization",
        "Model Info": "Model Information",
        "Error Analysis": "Error Analysis",
        "Explainability": "Explainability",
    }
    return page_map.get(selected, "Landing Page")


def main() -> None:
    page = sidebar_navigation()
    if page == "Landing Page":
        render_home_page()
    elif page == "Model Manager":
        render_model_manager_page()
    elif page == "Research: Model Agreement":
        render_model_agreement_page()
    elif page == "Research: Decision Trace":
        render_model_agreement_page()
    elif page == "Research: Calibration":
        render_calibration_page()
    elif page == "Research: Error Explorer":
        render_hard_examples_page()
    elif page == "Entity Detection":
        render_entity_analysis_page()
    elif page == "Intent Detection":
        render_intent_analysis_page()
    elif page == "Negation Detection":
        render_negation_analysis_page()
    elif page == "Contradiction Detection":
        render_contradiction_analysis_page()
    elif page == "Lexical Penalty":
        render_lexical_analysis_page()
    elif page == "Adaptive Ensemble V2":
        render_adaptive_ensemble_v2_page()
    elif page == "Advanced Calibration":
        render_calibration_v2_page()
    elif page == "Error Logger":
        render_error_logger_page()
    elif page == "Agreement Dashboard":
        render_agreement_dashboard_page()
    elif page == "Advanced Explainability":
        render_explainer_page()
    elif page == "Performance Optimizer":
        render_performance_optimizer_page()
    elif page == "Evaluation Suite":
        render_evaluation_page()
    elif page == "Hard Test Generator":
        render_hard_test_generator_page()
    elif page == "Project Overview":
        render_project_overview_page()
    elif page == "Dataset Information":
        render_dataset_page()
    elif page == "NLP Pipeline Visualization":
        render_pipeline_page()
    elif page == "Model Information":
        render_model_information_page()
    elif page == "Model Comparison":
        render_model_comparison_page()
    elif page == "Prediction Page":
        render_prediction_page()
    elif page == "Batch CSV Prediction":
        render_batch_prediction_page()
    elif page == "Performance Dashboard":
        render_dashboard_page()
    elif page == "Error Analysis":
        render_error_analysis_page()
    elif page == "Explainability":
        render_explainability_page()
    render_footer()


if __name__ == "__main__":
    main()
