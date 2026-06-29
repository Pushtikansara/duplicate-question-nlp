from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any

import matplotlib.pyplot as plt
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
    resolve_model_selection,
)
from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer
from duplicate_question_app.week2_inference import Week2InferenceService, is_week2_model, check_week2_artifacts
from duplicate_question_app.visuals import (
    create_batch_summary_figure,
    create_confusion_matrix_figure,
    create_pipeline_figure,
    create_probability_figure,
    create_roc_curve_figure,
)


st.set_page_config(
    page_title="Duplicate Question Detection",
    page_icon="NLP",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        .hero-card {
            padding: 1.3rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(37,99,235,0.12), rgba(14,165,233,0.08));
            border: 1px solid rgba(37,99,235,0.18);
            margin-bottom: 1rem;
        }
        .subtle-card {
            padding: 1rem 1.1rem;
            border-radius: 14px;
            border: 1px solid rgba(148,163,184,0.25);
            background: rgba(15,23,42,0.03);
            margin-bottom: 0.9rem;
        }
        .small-note {
            color: #64748B;
            font-size: 0.92rem;
        }
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
    merged.loc[
        (merged["true_label"] == 0) & (merged["predicted_label"] == 1),
        "error_type",
    ] = "False Positive"
    merged.loc[
        (merged["true_label"] == 1) & (merged["predicted_label"] == 0),
        "error_type",
    ] = "False Negative"
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
        for filename in (
            "fig1_threshold_tuning.png",
            "fig2_error_analysis.png",
            "fig3_ablation_comparison.png",
            "fig4_roc_comparison.png",
        )
    )
    return _get_week4_plot_paths(plot_signatures)


@st.cache_resource(show_spinner=False)
def get_inference_service(model_cache_key: str) -> tuple[Any, Any]:
    del model_cache_key
    selected = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    
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
        }
        return service, metadata
    
    # Handle transformer models (Week 3 and Week 4)
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
    service, metadata = get_inference_service(resolution.cache_key)
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    if isinstance(metadata, dict):
        model_label = metadata.get("model_label", "Unknown")
    elif hasattr(metadata, "model_label"):
        model_label = metadata.model_label
    else:
        model_label = "Unknown"
    
    if isinstance(metadata, dict):
        st.info(f"Active model: **{model_label}** | Threshold: **0.50** | Device: **CPU**")
    elif metadata.model_version == "week4":
        st.success(
            f"Active model: {metadata.model_label}. "
            f"Threshold source: {metadata.threshold_source}"
        )
    else:
        fallback_reason = metadata.fallback_reason or "Week 4 could not be activated."
        st.warning(
            f"Fallback active: {metadata.model_label}. {fallback_reason} "
            f"Using threshold {metadata.decision_threshold:.2f}."
        )

    if not isinstance(metadata, dict) and metadata.load_errors:
        st.info("Earlier load attempts: " + " | ".join(metadata.load_errors))


def build_model_status_table(resolution: Any) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for status in (resolution.week4, resolution.week3):
        rows.append(
            {
                "Model": status.label,
                "Directory": str(status.model_dir.relative_to(PROJECT_ROOT)),
                "Ready": "Yes" if status.ready else "No",
                "Config": "Yes" if status.has_config else "No",
                "Weights": status.weight_file.name if status.weight_file else "Missing",
                "Tokenizer": ", ".join(status.tokenizer_files) if status.tokenizer_files else "Missing",
                "Issues": ", ".join(status.issues) if status.issues else "None",
            }
        )
    
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
    
    rows.append(
        {
            "Model": "Week 2 Models (TF-IDF + LR/SVM)",
            "Directory": "models/week2_models/",
            "Ready": "Yes" if week2_ready else "No",
            "Config": "N/A",
            "Weights": "joblib files" if week2_ready else "Missing",
            "Tokenizer": "N/A",
            "Issues": ", ".join(week2_issues) if week2_issues else "None",
        }
    )
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
        "LR + TF-IDF": "TF-IDF + Logistic Regression",
        "SVM + TF-IDF": "TF-IDF + Linear SVM",
    }
    for source_name in ("LR + TF-IDF", "SVM + TF-IDF"):
        if not week2_df.empty and "Model" in week2_df.columns:
            match = week2_df[week2_df["Model"] == source_name]
        else:
            match = pd.DataFrame()
        row = match.iloc[0].to_dict() if not match.empty else {}
        rows.append(
            {
                "Model": week2_labels[source_name],
                "Accuracy": row.get("Accuracy"),
                "Precision": row.get("Precision (Dup)"),
                "Recall": row.get("Recall (Dup)"),
                "F1 Score": row.get("F1 (Dup)"),
                "ROC AUC": None,
                "Training Time": "N/A",
                "Model Size": "N/A",
                "Short Description": week2_descriptions[source_name],
            }
        )

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

    rows.append(
        {
            "Model": "DistilBERT (Week 3)",
            "Accuracy": week3_row.get("Accuracy"),
            "Precision": week3_row.get("Precision"),
            "Recall": week3_row.get("Recall"),
            "F1 Score": week3_row.get("F1 Score"),
            "ROC AUC": None,
            "Training Time": "N/A",
            "Model Size": _format_model_size(PATHS.week3_model_dir),
            "Short Description": "Fine-tuned DistilBERT sequence classifier used as the transformer baseline.",
        }
    )
    rows.append(
        {
            "Model": "Improved DistilBERT (Week 4)",
            "Accuracy": week4_row.get("Accuracy"),
            "Precision": week4_row.get("Precision"),
            "Recall": week4_row.get("Recall"),
            "F1 Score": week4_row.get("F1 Score"),
            "ROC AUC": week4_row.get("ROC-AUC"),
            "Training Time": "N/A",
            "Model Size": _format_model_size(PATHS.week4_model_dir),
            "Short Description": "Week 4 DistilBERT variant with class weighting, tuned threshold, and error-analysis artifacts.",
        }
    )

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
    st.caption(
        "Week 5 Streamlit application for Duplicate Question Detection. "
        "It automatically uses the Week 4 improved model when available and falls back to Week 3 otherwise."
    )


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
    """Return accuracy, precision, recall, f1 metrics for any of the 4 models."""
    if model_name == "TF-IDF + Logistic Regression (Week 2)":
        df = get_week2_model_comparison()
        if not df.empty and "Model" in df.columns:
            row = df[df["Model"] == "LR + TF-IDF"]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "accuracy": r.get("Accuracy"),
                    "precision": r.get("Precision (Dup)"),
                    "recall": r.get("Recall (Dup)"),
                    "f1": r.get("F1 (Dup)"),
                    "roc_auc": None,
                }
    elif model_name == "TF-IDF + Linear SVM (Week 2)":
        df = get_week2_model_comparison()
        if not df.empty and "Model" in df.columns:
            row = df[df["Model"] == "SVM + TF-IDF"]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "accuracy": r.get("Accuracy"),
                    "precision": r.get("Precision (Dup)"),
                    "recall": r.get("Recall (Dup)"),
                    "f1": r.get("F1 (Dup)"),
                    "roc_auc": None,
                }
    elif model_name == "DistilBERT (Week 3)":
        return get_transformer_metrics()
    elif model_name == "Improved DistilBERT (Week 4)":
        return get_week4_metrics()
    return {}


def render_home_page() -> None:
    selected_model = st.session_state.get("selected_model", "Improved DistilBERT (Week 4)")
    is_tf = is_transformer_model(selected_model)
    is_w2 = is_week2_model(selected_model)

    try:
        _, metadata, resolution = get_runtime_context()
    except Exception as exc:
        resolution = get_model_resolution()
        metadata = None

    try:
        summary = get_dataset_summary()
    except Exception as exc:
        summary = {"rows": 0, "duplicate_ratio": 0.0}
        st.warning(f"Dataset summary is unavailable: {exc}")

    active_metrics = get_model_metrics_for(selected_model)

    # Build model description based on type
    if is_tf and metadata and not isinstance(metadata, dict):
        model_desc = (
            f"Active model: <strong>{metadata.model_label}</strong> | "
            f"Decision threshold: <strong>{metadata.decision_threshold:.2f}</strong> | "
            f"Device: <strong>{metadata.device}</strong>"
        )
    elif is_w2:
        model_desc = (
            f"Active model: <strong>{selected_model}</strong> | "
            f"Decision threshold: <strong>0.50</strong> | "
            f"Device: <strong>CPU</strong>"
        )
    else:
        model_desc = f"Selected model: <strong>{selected_model}</strong>"

    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin-bottom:0.3rem;">Duplicate Question Detection System</h1>
            <p style="font-size:1.05rem; margin-bottom:0.6rem;">
                Production-ready application for Quora duplicate question detection.
            </p>
            <p class="small-note">
                {model_desc}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show runtime message for transformer models
    if is_tf and metadata and not isinstance(metadata, dict):
        render_model_runtime_message(metadata)

    # Show active metrics
    if active_metrics and any(v is not None for v in [active_metrics.get("accuracy"), active_metrics.get("f1")]):
        st.subheader(f"{selected_model} Performance")
        metric_card_row(active_metrics)
    else:
        st.info(f"Metrics for **{selected_model}** are not available yet. Run the training notebooks first.")

    week2_arts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_arts.values())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dataset Size", f"{summary['rows']:,}")
    col2.metric("Duplicate Ratio", safe_metric(summary["duplicate_ratio"]))
    col3.metric("Week 3 (DistilBERT)", "Ready" if resolution.week3.ready else "Missing")
    col4.metric("Week 4 (Improved)", "Ready" if resolution.week4.ready else "Missing")

    st.subheader("Compare All Models")
    st.write(
        "Use the sidebar to switch between models and see their performance metrics. "
        "The **Model Comparison** page shows all models side by side. "
        "All models support live prediction."
    )

    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.metric("Week 2 (LR/SVM)", "Ready" if week2_ready else "Run export script")
        col2.metric("Live Prediction", "Supported for all 4 models")


def render_project_overview_page() -> None:
    st.title("Project Overview")
    st.write(
        "This project identifies whether two questions express the same intent. "
        "The workflow evolved from data cleaning and classical NLP baselines to transformer fine-tuning and Week 4 improvements."
    )

    overview_col1, overview_col2 = st.columns([1.2, 1])
    with overview_col1:
        st.subheader("Week-by-Week Progress")
        st.markdown(
            """
            - **Week 1:** Data collection, cleaning, exploratory data analysis, and preprocessing
            - **Week 2:** TF-IDF, Word2Vec, Sentence-BERT features, and classical ML baselines
            - **Week 3:** DistilBERT fine-tuning with a reusable inference pipeline
            - **Week 4:** Threshold tuning, class imbalance handling, and error analysis
            - **Week 5:** Streamlit application, dashboarding, deployment assets, and production-oriented structure
            """
        )

    with overview_col2:
        st.subheader("Current App Behavior")
        st.markdown(
            """
            - Loads **Week 4 improved model** when its Hugging Face artifacts are present and loadable
            - Falls back to **Week 3 DistilBERT** automatically when Week 4 is incomplete or fails to load
            - Uses existing exported results from `results/` for dashboards and explainability
            - Reuses notebook logic through reusable Python modules under `src/duplicate_question_app`
            """
        )


def render_dataset_page() -> None:
    st.title("Dataset Information")
    try:
        df = get_dataset()
        summary = get_dataset_summary()
    except Exception as exc:
        st.error(f"Dataset could not be loaded: {exc}")
        st.info(
            "Expected dataset path: `data/cleaned_quora.parquet` (preferred) or `data/cleaned_quora.csv`."
        )
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
        missing_df = (
            pd.DataFrame.from_dict(summary["missing_values"], orient="index", columns=["missing_count"])
            .sort_values("missing_count", ascending=False)
        )
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
        st.markdown(
            """
            - **Input layer:** two user questions
            - **Tokenizer:** DistilBERT pair tokenization with `max_length=128`
            - **Classifier:** fine-tuned sequence classification head
            - **Post-processing:** probability computation, thresholding, confidence scoring
            - **Week 4 enhancement path:** class-weighted model and tuned threshold when assets become available
            """
        )


def render_model_information_page() -> None:
    st.title("Model Information")
    try:
        _, metadata, resolution = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return
    
    if isinstance(metadata, dict):
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", metadata.get("model_label", "Unknown"))
        col2.metric("Decision Threshold", f"{metadata.get('decision_threshold', 0.5):.2f}")
        col3.metric("Model Type", "Classical ML (TF-IDF + Linear Model)")
        
        st.subheader("Architecture Summary")
        st.dataframe(
            pd.DataFrame([{
                "Model Type": "TF-IDF + Logistic Regression / Linear SVM",
                "Feature Extraction": "TF-IDF with ngram_range=(1,2), max_features=5000",
                "Training Data": "Full Quora dataset (404,290 pairs)",
                "Label": "is_duplicate (binary)",
            }]),
            use_container_width=True, hide_index=True,
        )
    else:
        model_config = load_model_config(metadata.model_dir)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Model", metadata.model_label)
        col2.metric("Decision Threshold", f"{metadata.decision_threshold:.2f}")
        col3.metric("Threshold Source", metadata.threshold_source)

        render_model_runtime_message(metadata)

        if model_config:
            st.subheader("Architecture Summary")
            config_subset = {
                "Architecture": ", ".join(model_config.get("architectures") or []),
                "Model Type": model_config.get("model_type"),
                "Number of Labels": model_config.get("num_labels"),
                "Vocabulary Size": model_config.get("vocab_size"),
                "Hidden Size": model_config.get("dim", model_config.get("hidden_size")),
            }
            st.dataframe(pd.DataFrame([config_subset]), use_container_width=True, hide_index=True)

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
    else:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold
        device = metadata.device
    
    st.caption(
        f"Running live inference with **{model_label}** on **{device}**. "
        f"Decision threshold: **{decision_threshold:.2f}**."
    )

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

        st.success(
            f"Model decision: **{result['prediction']}** using **{result['model_label']}**."
        )
        probability_figure = create_probability_figure(
            prob_duplicate=float(result["prob_duplicate"]),
            threshold=float(result["threshold"]),
        )
        st.pyplot(probability_figure, clear_figure=True)



def _detect_question_columns(df: pd.DataFrame) -> tuple[str, str] | None:
    candidate_pairs = [
        ("q1", "q2"),
        ("question1", "question2"),
        ("sentence1", "sentence2"),
    ]
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
    else:
        model_label = metadata.model_label
        decision_threshold = metadata.decision_threshold

    st.caption(
        f"Batch inference uses **{model_label}** with threshold **{decision_threshold:.2f}**."
    )

    template_df = pd.DataFrame(
        {
            "q1": [
                "How do I learn Python?",
                "What is the capital of France?",
            ],
            "q2": [
                "How can I learn Python programming?",
                "Which city is the largest in France?",
            ],
        }
    )
    st.download_button(
        "Download CSV Template",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="duplicate_question_template.csv",
        mime="text/csv",
    )

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
        st.warning("Rows with empty question text will be skipped and marked in the downloadable output.")

    st.subheader("Preview")
    st.dataframe(batch_df.head(10), use_container_width=True)

    if st.button("Run Batch Prediction", use_container_width=True):
        if not valid_mask.any():
            st.error("No valid rows were found in the uploaded CSV.")
            return
        try:
            question_pairs = list(
                zip(
                    prepared_df.loc[valid_mask, question1_column],
                    prepared_df.loc[valid_mask, question2_column],
                )
            )
            with st.spinner(f"Processing {len(question_pairs)} pairs with {model_label}..."):
                if is_week2_model(selected_model):
                    valid_results_df = service.predict_batch(question_pairs, selected_model)
                else:
                    valid_results_df = service.predict_batch(question_pairs)
        except Exception as exc:
            st.error(f"Batch prediction failed: {exc}")
            return

        merged_results = batch_df.copy()
        merged_results["batch_status"] = "Skipped: empty question text"
        valid_index = prepared_df.index[valid_mask]
        merged_results.loc[valid_index, "batch_status"] = "Predicted"
        for column in valid_results_df.columns:
            merged_results[column] = pd.NA
            merged_results.loc[valid_index, column] = valid_results_df[column].to_numpy()

        st.success(f"Generated predictions for {len(merged_results):,} question pairs.")
        st.dataframe(merged_results, use_container_width=True)

        summary_figure = create_batch_summary_figure(merged_results[merged_results["batch_status"] == "Predicted"])
        st.pyplot(summary_figure, clear_figure=True)

        st.download_button(
            "Download Prediction Results",
            data=merged_results.to_csv(index=False).encode("utf-8"),
            file_name="duplicate_question_predictions.csv",
            mime="text/csv",
        )


def render_model_comparison_page() -> None:
    st.title("Model Comparison")
    st.write("Roadmap-level comparison across the Week 2 classical baselines, Week 3 transformer, and Week 4 improved transformer.")

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
        week4_f1 = week4_row.iloc[0]["F1 Score"]
        week3_f1 = week3_row.iloc[0]["F1 Score"]
        week4_accuracy = week4_row.iloc[0]["Accuracy"]
        week3_accuracy = week3_row.iloc[0]["Accuracy"]
        col1, col2 = st.columns(2)
        if not pd.isna(week4_f1) and not pd.isna(week3_f1):
            improvement = week4_f1 - week3_f1
            col1.metric("Week 4 F1", safe_metric(week4_f1), delta=f"{improvement:+.2%}")
        if not pd.isna(week4_accuracy) and not pd.isna(week3_accuracy):
            accuracy_improvement = week4_accuracy - week3_accuracy
            col2.metric("Week 4 Accuracy", safe_metric(week4_accuracy), delta=f"{accuracy_improvement:+.2%}")
    
    # Highlight best performing model
    st.subheader("🏆 Best Performing Model")
    if not comparison_df.empty:
        best_row = comparison_df.loc[comparison_df["F1 Score"].idxmax()] if "F1 Score" in comparison_df.columns and comparison_df["F1 Score"].notna().any() else None
        if best_row is not None and not pd.isna(best_row["F1 Score"]):
            st.success(f"**{best_row['Model']}** achieved the highest F1 Score: **{best_row['F1 Score']:.4f}**")
            st.caption(f"Accuracy: {best_row['Accuracy']:.4f} | Precision: {best_row['Precision']:.4f} | Recall: {best_row['Recall']:.4f}")


def render_dashboard_page() -> None:
    st.title("Performance Dashboard")
    week3_metrics = get_transformer_metrics()
    week4_metrics = get_week4_metrics()

    tab_week4, tab_week3, tab_compare = st.tabs(
        ["Week 4 (Improved)", "Week 3 (Baseline)", "Comparison"]
    )

    with tab_week4:
        if not week4_metrics:
            st.info("Week 4 prediction artifacts are not available, so Week 4 metrics cannot be computed.")
        else:
            metric_card_row(week4_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(
                    create_confusion_matrix_figure(week4_metrics["confusion_matrix"]),
                    clear_figure=True,
                )

            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week4_metrics.get("roc_curve")
                roc_auc = week4_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(
                        create_roc_curve_figure(
                            roc_curve_data["fpr"],
                            roc_curve_data["tpr"],
                            roc_auc,
                        ),
                        clear_figure=True,
                    )
                else:
                    st.info("ROC data is not available for Week 4 artifacts.")

            threshold_df = get_week4_threshold_df()
            if not threshold_df.empty and {"Threshold", "F1"}.issubset(threshold_df.columns):
                best_f1 = float(threshold_df["F1"].max())
                best_threshold = float(
                    threshold_df.loc[threshold_df["F1"] == best_f1, "Threshold"].astype(float).max()
                )
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
            st.warning("Week 3 prediction artifacts are missing, so the Week 3 dashboard cannot be rendered.")
        else:
            metric_card_row(week3_metrics)
            cm_col, roc_col = st.columns(2)
            with cm_col:
                st.subheader("Confusion Matrix")
                st.pyplot(
                    create_confusion_matrix_figure(week3_metrics["confusion_matrix"]),
                    clear_figure=True,
                )

            with roc_col:
                st.subheader("ROC Curve")
                roc_curve_data = week3_metrics.get("roc_curve")
                roc_auc = week3_metrics.get("roc_auc")
                if roc_curve_data and roc_auc is not None:
                    st.pyplot(
                        create_roc_curve_figure(
                            roc_curve_data["fpr"],
                            roc_curve_data["tpr"],
                            roc_auc,
                        ),
                        clear_figure=True,
                    )
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
                st.info("Week 2 vs Week 3 comparison file is not available.")

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
            display_cols = [
                col
                for col in [
                    "q1",
                    "q2",
                    "actual_class_name",
                    "predicted_class_name",
                    "confidence",
                    "prob_duplicate",
                    "error_type",
                ]
                if col in error_df.columns
            ]
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
    st.title("Explainability and Week 4 Outputs")
    week4_plots = get_week4_plot_paths()
    week4_threshold_df = get_week4_threshold_df()
    week4_ablation = get_week4_ablation_df()
    week4_predictions = get_week4_predictions_df()
    week4_metrics = get_week4_metrics()

    if not week4_plots and week4_threshold_df.empty and week4_ablation.empty and week4_predictions.empty:
        st.info(
            "Week 4 exported artifacts are not fully available yet. "
            "The app will automatically pick them up when the files are added."
        )
        return

    tab_overview, tab_threshold, tab_ablation, tab_predictions, tab_visuals = st.tabs(
        ["Overview", "Threshold Tuning", "Ablation", "Predictions", "Visuals"]
    )

    with tab_overview:
        if week4_metrics:
            metric_card_row(week4_metrics)
        st.write(
            "Week 4 focuses on threshold tuning, handling class imbalance, and deeper error analysis. "
            "This section renders the exported artifacts from `results/week4_improvement/`."
        )
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
                best_threshold = float(
                    week4_threshold_df.loc[week4_threshold_df["F1"] == best_f1, "Threshold"].astype(float).max()
                )
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


def sidebar_navigation() -> str:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        [
            "Landing Page",
            "Project Overview",
            "Dataset Information",
            "NLP Pipeline Visualization",
            "Model Information",
            "Model Comparison",
            "Prediction Page",
            "Batch CSV Prediction",
            "Performance Dashboard",
            "Error Analysis",
            "Explainability",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Model Selection")

    prev_model = st.session_state.get("selected_model", None)
    selected = st.sidebar.selectbox(
        "Choose a model",
        MODEL_CHOICES,
        index=MODEL_CHOICES.index(prev_model) if prev_model in MODEL_CHOICES else 3,
        key="selected_model_widget",
    )

    if selected != prev_model:
        st.session_state["selected_model"] = selected
        get_inference_service.clear()
        st.rerun()

    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "Improved DistilBERT (Week 4)"

    resolution = get_model_resolution()

    model_name = st.session_state["selected_model"]
    is_tf = is_transformer_model(model_name)

    try:
        _, metadata, _ = get_runtime_context()
        if isinstance(metadata, dict):
            st.sidebar.caption(f"Active: {metadata.get('model_label', 'Unknown')}")
            st.sidebar.caption(f"Threshold: {metadata.get('decision_threshold', 0.5):.2f}")
        else:
            st.sidebar.caption(f"Active: {metadata.model_label}")
            st.sidebar.caption(f"Threshold: {metadata.decision_threshold:.2f}")
    except Exception as exc:
        st.sidebar.error(f"Model load failed: {exc}")

    st.sidebar.markdown("---")
    week2_artifacts = check_week2_artifacts(PATHS)
    week2_ready = all(week2_artifacts.values())
    st.sidebar.caption(f"Week 2 (LR/SVM): {'✅' if week2_ready else '❌'}")
    st.sidebar.caption(f"Week 3 (DistilBERT): {'✅' if resolution.week3.ready else '❌'}")
    st.sidebar.caption(f"Week 4 (Improved): {'✅' if resolution.week4.ready else '❌'}")
    return page


def main() -> None:
    page = sidebar_navigation()

    if page == "Landing Page":
        render_home_page()
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
