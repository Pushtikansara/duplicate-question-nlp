from __future__ import annotations

import json
from pathlib import Path
import sys
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
    load_week2_vs_week3_comparison,
    load_week4_ablation,
    load_week4_predictions,
    load_week4_threshold_analysis,
    reconstruct_week3_test_frame,
)
from duplicate_question_app.config import get_app_paths, resolve_model_selection
from duplicate_question_app.inference import DuplicateQuestionInferenceService, load_model_and_tokenizer
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
def get_inference_service(model_cache_key: str) -> tuple[DuplicateQuestionInferenceService, Any]:
    del model_cache_key
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


def get_runtime_context() -> tuple[DuplicateQuestionInferenceService, Any, Any]:
    resolution = get_model_resolution()
    service, metadata = get_inference_service(resolution.cache_key)
    return service, metadata, resolution


def render_model_runtime_message(metadata: Any) -> None:
    if metadata.model_version == "week4":
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

    if metadata.load_errors:
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
    return pd.DataFrame(rows)


def safe_metric(value: Any, percent: bool = True, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.{decimals}%}"
    return f"{float(value):.{decimals}f}"


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


def render_home_page() -> None:
    try:
        _, metadata, resolution = get_runtime_context()
    except Exception as exc:
        st.title("Duplicate Question Detection System")
        st.error(f"Model could not be loaded: {exc}")
        st.info(
            "Verify that either `models/week4_improved_model/` or `models/saved_transformer_model/` "
            "contains Hugging Face `config.json` and model weights."
        )
        return

    try:
        summary = get_dataset_summary()
    except Exception as exc:
        summary = {"rows": 0, "duplicate_ratio": 0.0}
        st.warning(f"Dataset summary is unavailable: {exc}")

    week3_metrics = get_transformer_metrics()
    week4_metrics = get_week4_metrics()
    active_metrics = (
        week4_metrics if metadata.model_version == "week4" and week4_metrics else week3_metrics
    )

    st.markdown(
        f"""
        <div class="hero-card">
            <h1 style="margin-bottom:0.3rem;">Duplicate Question Detection System</h1>
            <p style="font-size:1.05rem; margin-bottom:0.6rem;">
                Production-ready Week 5 Streamlit application for Quora duplicate question detection.
            </p>
            <p class="small-note">
                Active model: <strong>{metadata.model_label}</strong> |
                Decision threshold: <strong>{metadata.decision_threshold:.2f}</strong> |
                Device: <strong>{metadata.device}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_model_runtime_message(metadata)
    metric_card_row(active_metrics)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dataset Size", f"{summary['rows']:,}")
    col2.metric("Duplicate Ratio", safe_metric(summary["duplicate_ratio"]))
    col3.metric("Week 4 Ready", "Yes" if resolution.week4.ready else "No")
    col4.metric("Week 3 Ready", "Yes" if resolution.week3.ready else "No")

    st.subheader("What This App Includes")
    st.write(
        "Landing page, project overview, dataset inspection, pipeline visualization, "
        "single prediction, batch CSV prediction, downloads, performance dashboard, "
        "error analysis, and Week 4 explainability assets when they exist."
    )

    with st.container(border=True):
        st.write("Use the sidebar to navigate through each Week 5 deliverable.")
        if resolution.fallback_reason:
            st.caption(f"Fallback condition: {resolution.fallback_reason}")


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
    model_config = load_model_config(metadata.model_dir)

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Model", metadata.model_label)
    col2.metric("Decision Threshold", f"{metadata.decision_threshold:.2f}")
    col3.metric("Threshold Source", metadata.threshold_source)

    render_model_runtime_message(metadata)

    st.subheader("Resolution Logic")
    st.markdown(
        f"""
        - **Week 4 ready:** `{resolution.week4.ready}`
        - **Week 3 ready:** `{resolution.week3.ready}`
        - **Selected model directory:** `{metadata.model_dir}`
        - **Cache key:** `{metadata.cache_key}`
        """
    )

    st.subheader("Artifact Inventory")
    st.dataframe(build_model_status_table(resolution), use_container_width=True, hide_index=True)

    if model_config:
        st.subheader("Config Snapshot")
        config_subset = {
            "architectures": model_config.get("architectures"),
            "model_type": model_config.get("model_type"),
            "num_labels": model_config.get("num_labels"),
            "vocab_size": model_config.get("vocab_size"),
            "hidden_size": model_config.get("dim", model_config.get("hidden_size")),
            "dropout": model_config.get("seq_classif_dropout", model_config.get("dropout")),
        }
        st.json(config_subset)

    st.subheader("Saved Artifacts")
    artifact_files = sorted(path.name for path in metadata.model_dir.glob("*"))
    st.write(artifact_files)


def render_prediction_page() -> None:
    st.title("Prediction Page")
    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    st.caption(
        f"Running live inference with {metadata.model_label} on {metadata.device}. "
        f"Decision threshold: {metadata.decision_threshold:.2f}."
    )

    with st.form("single_prediction_form"):
        question1 = st.text_area("Question 1", placeholder="Enter the first question", height=120)
        question2 = st.text_area("Question 2", placeholder="Enter the second question", height=120)
        submitted = st.form_submit_button("Predict Duplicate Status", use_container_width=True)

    if submitted:
        if not question1.strip() or not question2.strip():
            st.error("Both question fields are required.")
            return

        with st.spinner(f"Running inference with {metadata.model_label}..."):
            try:
                result = service.predict_single(question1, question2)
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
                return

        col1, col2, col3 = st.columns(3)
        col1.metric("Prediction", result["prediction"])
        col2.metric("Confidence", f"{result['confidence']:.2%}")
        col3.metric("Threshold", f"{result['threshold']:.2f}")

        st.success(
            f"Model decision: **{result['prediction']}** using {result['model_label']}."
        )
        probability_figure = create_probability_figure(
            prob_duplicate=float(result["prob_duplicate"]),
            threshold=float(result["threshold"]),
        )
        st.pyplot(probability_figure, clear_figure=True)

        with st.expander("Raw Prediction Details"):
            st.json(result)


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
    try:
        service, metadata, _ = get_runtime_context()
    except Exception as exc:
        st.error(f"Model could not be loaded: {exc}")
        return

    st.caption(
        f"Batch inference uses {metadata.model_label} with threshold {metadata.decision_threshold:.2f}."
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
            with st.spinner(f"Processing {len(question_pairs)} pairs with {metadata.model_label}..."):
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
        rows: list[dict[str, object]] = []
        if week3_metrics:
            rows.append(
                {
                    "Model": "Week 3 DistilBERT",
                    "Accuracy": week3_metrics.get("accuracy"),
                    "Precision": week3_metrics.get("precision"),
                    "Recall": week3_metrics.get("recall"),
                    "F1": week3_metrics.get("f1"),
                    "ROC-AUC": week3_metrics.get("roc_auc"),
                }
            )
        if week4_metrics:
            rows.append(
                {
                    "Model": "Week 4 Improved DistilBERT",
                    "Accuracy": week4_metrics.get("accuracy"),
                    "Precision": week4_metrics.get("precision"),
                    "Recall": week4_metrics.get("recall"),
                    "F1": week4_metrics.get("f1"),
                    "ROC-AUC": week4_metrics.get("roc_auc"),
                }
            )

        if not rows:
            st.info("No evaluation artifacts are available to build a comparison table yet.")
        else:
            comparison_table = pd.DataFrame(rows).set_index("Model")
            st.dataframe(comparison_table, use_container_width=True)
            chart_df = comparison_table[["Accuracy", "Precision", "Recall", "F1"]].copy()
            st.bar_chart(chart_df)
            if len(comparison_table) == 2:
                delta_f1 = comparison_table.loc["Week 4 Improved DistilBERT", "F1"] - comparison_table.loc["Week 3 DistilBERT", "F1"]
                delta_accuracy = comparison_table.loc["Week 4 Improved DistilBERT", "Accuracy"] - comparison_table.loc["Week 3 DistilBERT", "Accuracy"]
                col1, col2 = st.columns(2)
                col1.metric("F1 Improvement", safe_metric(comparison_table.loc["Week 4 Improved DistilBERT", "F1"]), delta=f"{delta_f1:+.2%}")
                col2.metric("Accuracy Improvement", safe_metric(comparison_table.loc["Week 4 Improved DistilBERT", "Accuracy"]), delta=f"{delta_accuracy:+.2%}")


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
            normalized_error = working["error_type"].astype(str)
            normalized_error = normalized_error.str.replace(" ✅", "", regex=False).str.replace(" ❌", "", regex=False)
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


def render_developer_page() -> None:
    st.title("About Developer")
    st.write(
        "This Streamlit application packages the notebook-based NLP workflow into a reusable "
        "project structure that supports both coursework presentation and production-style inference."
    )
    st.markdown(
        """
        - **App architecture:** reusable modules in `src/duplicate_question_app`
        - **Inference support:** single and batch prediction with threshold-based decisions
        - **Fallback behavior:** Week 4 model when available, Week 3 otherwise
        - **Deployment support:** root `requirements.txt` and `.streamlit/config.toml`
        """
    )


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
            "Prediction Page",
            "Batch CSV Prediction",
            "Performance Dashboard",
            "Error Analysis",
            "Explainability",
            "About Developer",
        ],
    )

    resolution = get_model_resolution()
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Week 4 model available: {resolution.week4.ready}")
    st.sidebar.caption(f"Week 3 model available: {resolution.week3.ready}")
    st.sidebar.caption(f"Week 4 plots detected: {len(get_week4_plot_paths())}")
    try:
        _, metadata, _ = get_runtime_context()
        st.sidebar.caption(f"Active model: {metadata.model_label}")
        st.sidebar.caption(f"Threshold: {metadata.decision_threshold:.2f}")
    except Exception as exc:
        st.sidebar.error(f"Model load failed: {exc}")
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
    else:
        render_developer_page()

    render_footer()


if __name__ == "__main__":
    main()
