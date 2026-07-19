"""Evaluation Module — comprehensive evaluation with automated report generation.

Generates:
- Confusion Matrix
- ROC Curve
- Precision-Recall Curve
- Calibration Curve (Reliability Diagram)
- Top 100 hardest failures
- Per-model comparison
- False Positive / False Negative reports
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
    brier_score_loss,
    log_loss,
    classification_report,
)

try:
    from sklearn.calibration import calibration_curve
    _CALIBRATION_AVAILABLE = True
except ImportError:
    _CALIBRATION_AVAILABLE = False


@dataclass
class EvaluationMetrics:
    """Complete evaluation metrics for a model."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    log_loss: float
    ece: float              # Expected Calibration Error
    mce: float              # Maximum Calibration Error
    confusion_matrix: np.ndarray
    classification_report: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1': self.f1,
            'roc_auc': self.roc_auc,
            'pr_auc': self.pr_auc,
            'brier_score': self.brier_score,
            'log_loss': self.log_loss,
            'ece': self.ece,
            'mce': self.mce,
            'confusion_matrix': self.confusion_matrix.tolist(),
            'classification_report': self.classification_report,
        }


@dataclass
class HardExample:
    """A single hard example with analysis."""
    index: int
    q1: str
    q2: str
    true_label: int
    predicted_label: int
    prob_duplicate: float
    confidence: float
    error_type: str           # 'FP' or 'FN'
    hardness_score: float     # Distance from decision boundary
    error_categories: List[str]
    model_votes: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'q1': self.q1,
            'q2': self.q2,
            'true_label': self.true_label,
            'predicted_label': self.predicted_label,
            'prob_duplicate': self.prob_duplicate,
            'confidence': self.confidence,
            'error_type': self.error_type,
            'hardness_score': self.hardness_score,
            'error_categories': self.error_categories,
            'model_votes': self.model_votes,
        }


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error."""
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if not mask.any():
            continue
        bin_conf = probs[mask].mean()
        bin_acc = labels[mask].mean()
        ece += np.abs(bin_acc - bin_conf) * mask.sum()
    return float(ece / len(probs)) if len(probs) > 0 else 0.0


def compute_mce(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Maximum Calibration Error."""
    if len(probs) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    max_error = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_boundaries[i]) & (probs < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (probs >= bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if not mask.any():
            continue
        bin_conf = probs[mask].mean()
        bin_acc = labels[mask].mean()
        error = np.abs(bin_acc - bin_conf)
        max_error = max(max_error, error)
    return float(max_error)


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    model_name: str = "Model",
) -> EvaluationMetrics:
    """Compute comprehensive evaluation metrics."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    try:
        roc_auc = auc(*roc_curve(y_true, y_prob)[:2])
    except ValueError:
        roc_auc = 0.0

    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except ValueError:
        pr_auc = 0.0

    brier = brier_score_loss(y_true, y_prob)
    ll = log_loss(y_true, y_prob, labels=[0, 1])
    ece = compute_ece(y_prob, y_true)
    mce = compute_mce(y_prob, y_true)

    report = classification_report(y_true, y_pred, target_names=['Non-Duplicate', 'Duplicate'])

    return EvaluationMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        pr_auc=pr_auc,
        brier_score=brier,
        log_loss=ll,
        ece=ece,
        mce=mce,
        confusion_matrix=cm,
        classification_report=report,
    )


def find_hard_examples(
    df: pd.DataFrame,
    prob_col: str = 'prob_duplicate',
    pred_col: str = 'predicted_label',
    true_col: str = 'true_label',
    q1_col: str = 'q1',
    q2_col: str = 'q2',
    top_k: int = 100,
    include_model_votes: bool = False,
) -> Tuple[List[HardExample], List[HardExample]]:
    """Find top-k hardest false positives and false negatives."""
    false_positives = []
    false_negatives = []

    for idx, row in df.iterrows():
        true_label = row[true_col]
        pred_label = row[pred_col]
        prob = row[prob_col]
        confidence = max(prob, 1 - prob)

        if true_label == 0 and pred_label == 1:
            # False Positive
            hardness = prob  # High prob for non-duplicate = hard
            error_type = 'FP'
            false_positives.append((hardness, idx, row))
        elif true_label == 1 and pred_label == 0:
            # False Negative
            hardness = 1 - prob  # Low prob for duplicate = hard
            error_type = 'FN'
            false_negatives.append((hardness, idx, row))

    # Sort by hardness (descending)
    false_positives.sort(key=lambda x: x[0], reverse=True)
    false_negatives.sort(key=lambda x: x[0], reverse=True)

    def make_hard_example(hardness: float, idx: int, row: pd.Series, error_type: str) -> HardExample:
        categories = []
        # Add error categories based on text analysis
        q1 = str(row.get(q1_col, ''))
        q2 = str(row.get(q2_col, ''))

        # Simple heuristics for error categories
        q1_lower, q2_lower = q1.lower(), q2.lower()

        # Check for language mismatch
        langs = ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'swift']
        q1_langs = {l for l in langs if l in q1_lower}
        q2_langs = {l for l in langs if l in q2_lower}
        if q1_langs and q2_langs and q1_langs != q2_langs:
            categories.append('language_mismatch')

        # Check for framework mismatch
        fws = ['tensorflow', 'pytorch', 'keras', 'django', 'flask', 'spring', 'react', 'vue', 'angular']
        q1_fws = {f for f in fws if f in q1_lower}
        q2_fws = {f for f in fws if f in q2_lower}
        if q1_fws and q2_fws and q1_fws != q2_fws:
            categories.append('framework_mismatch')

        # Check for negation
        neg_words = ['not', 'no', 'never', 'without', 'remove', 'disable', 'uninstall', 'delete', 'stop']
        q1_neg = any(w in q1_lower.split() for w in neg_words)
        q2_neg = any(w in q2_lower.split() for w in neg_words)
        if q1_neg != q2_neg:
            categories.append('negation_mismatch')

        # Check for install/uninstall
        if 'install' in q1_lower and 'uninstall' in q2_lower:
            categories.append('install_uninstall')
        if 'uninstall' in q1_lower and 'install' in q2_lower:
            categories.append('install_uninstall')

        model_votes = {}
        if include_model_votes:
            for col in row.index:
                if 'prob' in col.lower() or 'vote' in col.lower():
                    model_votes[col] = float(row[col]) if pd.notna(row[col]) else 0.5

        return HardExample(
            index=idx,
            q1=q1,
            q2=q2,
            true_label=true_label,
            predicted_label=pred_label,
            prob_duplicate=float(prob),
            confidence=float(confidence),
            error_type=error_type,
            hardness_score=float(hardness),
            error_categories=categories,
            model_votes=model_votes,
        )

    fps = [make_hard_example(h, i, r, 'FP') for h, i, r in false_positives[:top_k]]
    fns = [make_hard_example(h, i, r, 'FN') for h, i, r in false_negatives[:top_k]]

    return fps, fns


def generate_evaluation_report(
    predictions_df: pd.DataFrame,
    output_dir: Path,
    model_name: str = "Model",
    prob_col: str = 'prob_duplicate',
    pred_col: str = 'predicted_label',
    true_col: str = 'true_label',
    q1_col: str = 'q1',
    q2_col: str = 'q2',
) -> Dict[str, Any]:
    """Generate comprehensive evaluation report with plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    y_true = predictions_df[true_col].values
    y_pred = predictions_df[pred_col].values
    y_prob = predictions_df[prob_col].values

    # Compute metrics
    metrics = evaluate_model(y_true, y_pred, y_prob, model_name)

    # Find hard examples
    fps, fns = find_hard_examples(
        predictions_df,
        prob_col=prob_col,
        pred_col=pred_col,
        true_col=true_col,
        q1_col=q1_col,
        q2_col=q2_col,
        top_k=100,
    )

    # Generate plots
    plot_paths = {}

    # 1. Confusion Matrix
    cm_path = output_dir / f"{model_name}_confusion_matrix.png"
    plot_confusion_matrix(metrics.confusion_matrix, cm_path, model_name)
    plot_paths['confusion_matrix'] = str(cm_path)

    # 2. ROC Curve
    roc_path = output_dir / f"{model_name}_roc_curve.png"
    plot_roc_curve(y_true, y_prob, roc_path, model_name, metrics.roc_auc)
    plot_paths['roc_curve'] = str(roc_path)

    # 3. Precision-Recall Curve
    pr_path = output_dir / f"{model_name}_pr_curve.png"
    plot_pr_curve(y_true, y_prob, pr_path, model_name, metrics.pr_auc)
    plot_paths['pr_curve'] = str(pr_path)

    # 4. Calibration Curve
    cal_path = output_dir / f"{model_name}_calibration_curve.png"
    plot_calibration_curve(y_true, y_prob, cal_path, model_name)
    plot_paths['calibration_curve'] = str(cal_path)

    # 5. Prediction Distribution
    dist_path = output_dir / f"{model_name}_prediction_distribution.png"
    plot_prediction_distribution(y_prob, y_true, dist_path, model_name)
    plot_paths['prediction_distribution'] = str(dist_path)

    # 6. Error Analysis
    error_path = output_dir / f"{model_name}_error_analysis.png"
    plot_error_analysis(fps, fns, error_path, model_name)
    plot_paths['error_analysis'] = str(error_path)

    # Save metrics
    metrics_path = output_dir / f"{model_name}_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics.to_dict(), f, indent=2)

    # Save hard examples
    hard_examples_path = output_dir / f"{model_name}_hard_examples.json"
    hard_data = {
        'false_positives': [e.to_dict() for e in fps],
        'false_negatives': [e.to_dict() for e in fns],
    }
    with open(hard_examples_path, 'w') as f:
        json.dump(hard_data, f, indent=2)

    # Save CSV for easy analysis
    fp_df = pd.DataFrame([e.to_dict() for e in fps])
    fn_df = pd.DataFrame([e.to_dict() for e in fns])
    if not fp_df.empty:
        fp_df.to_csv(output_dir / f"{model_name}_false_positives.csv", index=False)
    if not fn_df.empty:
        fn_df.to_csv(output_dir / f"{model_name}_false_negatives.csv", index=False)

    # Generate summary report
    summary = {
        'model_name': model_name,
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics.to_dict(),
        'num_false_positives': len(fps),
        'num_false_negatives': len(fns),
        'hard_fp_categories': _categorize_errors(fps),
        'hard_fn_categories': _categorize_errors(fns),
        'plots': plot_paths,
        'artifacts': {
            'metrics': str(metrics_path),
            'hard_examples': str(hard_examples_path),
        },
    }

    summary_path = output_dir / f"{model_name}_evaluation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary


def _categorize_errors(examples: List[HardExample]) -> Dict[str, int]:
    """Count error categories."""
    cats = {}
    for ex in examples:
        for cat in ex.error_categories:
            cats[cat] = cats.get(cat, 0) + 1
    return cats


def plot_confusion_matrix(
    cm: np.ndarray,
    save_path: Path,
    title: str = "Confusion Matrix",
) -> None:
    """Plot confusion matrix."""
    fig, ax = plt.subplots(figsize=(6, 5))
    labels = ['Non-Duplicate', 'Duplicate']
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=labels, yticklabels=labels, ax=ax,
    )
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    save_path: Path,
    title: str = "ROC Curve",
    roc_auc: float = 0.0,
) -> None:
    """Plot ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, linewidth=2, label=f'ROC-AUC = {roc_auc:.3f}')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title(title)
    ax.legend(loc='lower right')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_pr_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    save_path: Path,
    title: str = "Precision-Recall Curve",
    pr_auc: float = 0.0,
) -> None:
    """Plot Precision-Recall curve."""
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, linewidth=2, label=f'PR-AUC = {pr_auc:.3f}')
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(title)
    ax.legend(loc='lower left')
    ax.grid(alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    save_path: Path,
    title: str = "Calibration Curve",
    n_bins: int = 10,
) -> None:
    """Plot calibration curve (reliability diagram)."""
    if not _CALIBRATION_AVAILABLE:
        # Manual calibration curve
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
        bin_accuracies = []

        for i in range(n_bins):
            mask = (y_prob >= bin_boundaries[i]) & (y_prob < bin_boundaries[i + 1])
            if i == n_bins - 1:
                mask = (y_prob >= bin_boundaries[i]) & (y_prob <= bin_boundaries[i + 1])
            if mask.any():
                bin_accuracies.append(y_true[mask].mean())
            else:
                bin_accuracies.append(np.nan)
        bin_accuracies = np.array(bin_accuracies)
    else:
        bin_accuracies, bin_centers = calibration_curve(y_true, y_prob, n_bins=n_bins)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect calibration')
    ax.plot(bin_centers, bin_accuracies, 'o-', linewidth=2, markersize=8, label='Model')
    ax.set_xlabel('Mean Predicted Probability')
    ax.set_ylabel('Fraction of Positives')
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_prediction_distribution(
    y_prob: np.ndarray,
    y_true: np.ndarray,
    save_path: Path,
    title: str = "Prediction Distribution",
) -> None:
    """Plot prediction probability distribution by class."""
    fig, ax = plt.subplots(figsize=(8, 5))
    probs_neg = y_prob[y_true == 0]
    probs_pos = y_prob[y_true == 1]

    bins = np.linspace(0, 1, 21)
    ax.hist(probs_neg, bins=bins, alpha=0.6, label='Non-Duplicate (true)', color='#64748B', density=True)
    ax.hist(probs_pos, bins=bins, alpha=0.6, label='Duplicate (true)', color='#2563EB', density=True)
    ax.axvline(0.5, color='#DC2626', linestyle='--', linewidth=2, label='Threshold = 0.5')
    ax.set_xlabel('Predicted Probability (Duplicate)')
    ax.set_ylabel('Density')
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_error_analysis(
    fps: List[HardExample],
    fns: List[HardExample],
    save_path: Path,
    title: str = "Error Analysis",
) -> None:
    """Plot error analysis breakdown."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # FP categories
    fp_cats = _categorize_errors(fps)
    if fp_cats:
        axes[0, 0].bar(fp_cats.keys(), fp_cats.values(), color='#EF4444', alpha=0.7)
        axes[0, 0].set_title('False Positive Categories')
        axes[0, 0].tick_params(axis='x', rotation=45)
    else:
        axes[0, 0].text(0.5, 0.5, 'No FPs', ha='center', va='center')

    # FN categories
    fn_cats = _categorize_errors(fns)
    if fn_cats:
        axes[0, 1].bar(fn_cats.keys(), fn_cats.values(), color='#3B82F6', alpha=0.7)
        axes[0, 1].set_title('False Negative Categories')
        axes[0, 1].tick_params(axis='x', rotation=45)
    else:
        axes[0, 1].text(0.5, 0.5, 'No FNs', ha='center', va='center')

    # FP hardness distribution
    fp_hardness = [e.hardness_score for e in fps]
    if fp_hardness:
        axes[1, 0].hist(fp_hardness, bins=20, color='#EF4444', alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('FP Hardness Distribution')
        axes[1, 0].set_xlabel('Hardness Score')
        axes[1, 0].set_ylabel('Count')

    # FN hardness distribution
    fn_hardness = [e.hardness_score for e in fns]
    if fn_hardness:
        axes[1, 1].hist(fn_hardness, bins=20, color='#3B82F6', alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('FN Hardness Distribution')
        axes[1, 1].set_xlabel('Hardness Score')
        axes[1, 1].set_ylabel('Count')

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def compare_models(
    predictions_dict: Dict[str, pd.DataFrame],
    true_col: str = 'true_label',
    prob_col: str = 'prob_duplicate',
    pred_col: str = 'predicted_label',
) -> pd.DataFrame:
    """Compare multiple models on the same test set."""
    results = []

    for model_name, df in predictions_dict.items():
        y_true = df[true_col].values
        y_pred = df[pred_col].values
        y_prob = df[prob_col].values

        metrics = evaluate_model(y_true, y_pred, y_prob, model_name)

        results.append({
            'Model': model_name,
            'Accuracy': metrics.accuracy,
            'Precision': metrics.precision,
            'Recall': metrics.recall,
            'F1': metrics.f1,
            'ROC-AUC': metrics.roc_auc,
            'PR-AUC': metrics.pr_auc,
            'Brier Score': metrics.brier_score,
            'Log Loss': metrics.log_loss,
            'ECE': metrics.ece,
            'MCE': metrics.mce,
        })

    return pd.DataFrame(results)


def generate_model_comparison_plots(
    predictions_dict: Dict[str, pd.DataFrame],
    output_dir: Path,
    true_col: str = 'true_label',
    prob_col: str = 'prob_duplicate',
) -> Dict[str, str]:
    """Generate comparison plots for multiple models."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_paths = {}

    # ROC comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    for model_name, df in predictions_dict.items():
        y_true = df[true_col].values
        y_prob = df[prob_col].values
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, linewidth=2, label=f'{model_name} (AUC={roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve Comparison')
    ax.legend()
    ax.grid(alpha=0.3)
    roc_path = output_dir / "roc_comparison.png"
    fig.savefig(roc_path, dpi=150)
    plt.close(fig)
    plot_paths['roc_comparison'] = str(roc_path)

    # PR comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    for model_name, df in predictions_dict.items():
        y_true = df[true_col].values
        y_prob = df[prob_col].values
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        pr_auc = average_precision_score(y_true, y_prob)
        ax.plot(recall, precision, linewidth=2, label=f'{model_name} (AUC={pr_auc:.3f})')
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title('Precision-Recall Curve Comparison')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    pr_path = output_dir / "pr_comparison.png"
    fig.savefig(pr_path, dpi=150)
    plt.close(fig)
    plot_paths['pr_comparison'] = str(pr_path)

    # Calibration comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect')
    for model_name, df in predictions_dict.items():
        y_true = df[true_col].values
        y_prob = df[prob_col].values
        if _CALIBRATION_AVAILABLE:
            frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10)
        else:
            bin_boundaries = np.linspace(0, 1, 11)
            mean_pred = []
            frac_pos = []
            for i in range(10):
                mask = (y_prob >= bin_boundaries[i]) & (y_prob < bin_boundaries[i + 1])
                if i == 9:
                    mask = (y_prob >= bin_boundaries[i]) & (y_prob <= bin_boundaries[i + 1])
                if mask.any():
                    mean_pred.append(y_prob[mask].mean())
                    frac_pos.append(y_true[mask].mean())
            mean_pred = np.array(mean_pred)
            frac_pos = np.array(frac_pos)
        ax.plot(mean_pred, frac_pos, 'o-', linewidth=2, markersize=6, label=model_name)
    ax.set_xlabel('Mean Predicted Probability')
    ax.set_ylabel('Fraction of Positives')
    ax.set_title('Calibration Curve Comparison')
    ax.legend()
    ax.grid(alpha=0.3)
    cal_path = output_dir / "calibration_comparison.png"
    fig.savefig(cal_path, dpi=150)
    plt.close(fig)
    plot_paths['calibration_comparison'] = str(cal_path)

    return plot_paths