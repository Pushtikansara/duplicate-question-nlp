from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.utils.constants import PATHS
from duplicate_question_app._artifacts import (
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


def path_signature(path: Path) -> str:
    if not path.exists():
        return f"{path.name}:missing"
    stat = path.stat()
    return f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}"


@st.cache_data(show_spinner=False)
def _get_dataset(dataset_signature: str) -> pd.DataFrame:
    del dataset_signature
    return load_dataset_frame(PATHS)


def _find_dataset_path() -> Path:
    from duplicate_question_app._artifacts.loader import _discover_data_file

    found = _discover_data_file(PATHS.data_dir)
    if found is not None:
        return found
    return PATHS.data_dir / "cleaned_quora.parquet"


def get_dataset() -> pd.DataFrame:
    return _get_dataset(path_signature(_find_dataset_path()))


@st.cache_data(show_spinner=False)
def _get_dataset_summary(dataset_signature: str) -> dict[str, Any]:
    del dataset_signature
    return build_dataset_summary(get_dataset())


def get_dataset_summary() -> dict[str, Any]:
    return _get_dataset_summary(path_signature(_find_dataset_path()))


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
    return _get_week3_test_frame(path_signature(_find_dataset_path()))


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
    predictions_path = PATHS.transformer_results_dir / "transformer_test_predictions.csv"
    return _get_week3_analysis_frame(path_signature(_find_dataset_path()), path_signature(predictions_path))


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
