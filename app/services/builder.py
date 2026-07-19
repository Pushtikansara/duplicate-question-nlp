from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.data import (
    get_transformer_metrics,
    get_week2_model_comparison,
    get_week2_vs_week3,
    get_week4_ablation_df,
    get_week4_metrics,
)
from app.utils.constants import PATHS, PROJECT_ROOT
from duplicate_question_app.week2_inference import check_week2_artifacts


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
    for m_name, m_dir in [
        ("BGE-base-en-v1.5", PATHS.bge_model_dir),
        ("E5-base-v2", PATHS.e5_model_dir),
        ("MPNet-base-v2", PATHS.mpnet_model_dir),
        ("DeBERTa-v3 Cross-Encoder", PATHS.deberta_model_dir),
        ("Cross-Encoder-Quora (Trained)", PATHS.finetuned_cross_encoder_dir),
    ]:
        exists = m_dir.exists() and (m_dir / "config.json").exists()
        rows.append(
            {
                "Model": m_name,
                "Directory": str(m_dir.relative_to(PROJECT_ROOT)) if m_dir.exists() else str(m_dir),
                "Ready": "Yes (via HuggingFace)" if not exists else "Yes (local)",
                "Config": "N/A (HF)",
                "Weights": "N/A (HF)",
                "Tokenizer": "N/A (HF)",
                "Issues": "Will download from HuggingFace on first use" if not exists else "None",
            }
        )
    return pd.DataFrame(rows)


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

    phase2_models = [
        ("BGE-base-en-v1.5", "BGE embedding model for semantic similarity."),
        ("E5-base-v2", "E5 embedding model with contrastive learning."),
        ("MPNet-base-v2", "MPNet masked and permuted language modeling."),
        ("DeBERTa-v3 Cross-Encoder", "Cross-encoder with disentangled attention."),
        ("Semantic Ensemble", "Averaged predictions from all models."),
    ]
    for name, desc in phase2_models:
        rows.append(
            {
                "Model": name,
                "Accuracy": None,
                "Precision": None,
                "Recall": None,
                "F1 Score": None,
                "ROC AUC": None,
                "Training Time": "N/A",
                "Model Size": "Varies",
                "Short Description": desc,
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


def _format_optional_metric(value: Any, percent: bool = True) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if percent:
        return f"{float(value):.2%}"
    return f"{float(value):.2f}"


def get_model_metrics_for(model_name: str) -> dict[str, Any]:
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
