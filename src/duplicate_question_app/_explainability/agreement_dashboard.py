"""Model Agreement Dashboard — advanced model agreement analysis.

Provides:
- Agreement percentage across models
- Confidence spread (min, max, mean, std)
- Entropy of model predictions
- Variance of probabilities
- Strongest model (highest confidence correct predictions)
- Weakest model (lowest confidence / most errors)
- Most influential model (largest impact on ensemble)
- Per-model calibration status
- Pairwise model agreement matrix
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from enum import Enum

from duplicate_question_app.agreement_engine import ModelVote, AgreementReport, get_agreement_report
from duplicate_question_app.config import AppPaths, get_app_paths


class ModelStrength(Enum):
    STRONGEST = "strongest"
    WEAKEST = "weakest"
    MOST_INFLUENTIAL = "most_influential"
    MOST_CALIBRATED = "most_calibrated"
    LEAST_CALIBRATED = "least_calibrated"


@dataclass
class ModelProfile:
    """Profile of a single model's behavior."""
    name: str
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    confidence_std: float = 0.0
    avg_prob_duplicate: float = 0.0
    prob_std: float = 0.0
    ece: float = 0.0  # Expected Calibration Error
    brier_score: float = 0.0
    agreement_with_ensemble: float = 0.0
    influence_score: float = 0.0
    is_borderline: float = 0.0  # Fraction of predictions near 0.5
    overconfidence: float = 0.0  # Confidence - accuracy when wrong

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'accuracy': self.accuracy,
            'avg_confidence': self.avg_confidence,
            'confidence_std': self.confidence_std,
            'avg_prob_duplicate': self.avg_prob_duplicate,
            'prob_std': self.prob_std,
            'ece': self.ece,
            'brier_score': self.brier_score,
            'agreement_with_ensemble': self.agreement_with_ensemble,
            'influence_score': self.influence_score,
            'is_borderline': self.is_borderline,
            'overconfidence': self.overconfidence,
        }


@dataclass
class AgreementDashboard:
    """Complete model agreement dashboard for a question pair."""
    # Overall agreement
    agreement_percentage: float
    unanimous: bool
    num_models_agreeing: int
    num_models_total: int

    # Confidence statistics
    confidence_mean: float
    confidence_std: float
    confidence_min: float
    confidence_max: float
    confidence_spread: float  # max - min

    # Entropy
    prediction_entropy: float  # Entropy of vote distribution
    probability_entropy: float  # Entropy of probability distribution

    # Variance
    probability_variance: float
    probability_std: float

    # Per-model details
    model_votes: List[Dict[str, Any]]
    models_agreeing: List[str]
    models_disagreeing: List[str]

    # Ensemble info
    ensemble_prob: float
    ensemble_method: str

    # Calibration info
    calibration_status: Dict[str, str]  # model -> "calibrated" / "overconfident" / "underconfident"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agreement_percentage': self.agreement_percentage,
            'unanimous': self.unanimous,
            'num_models_agreeing': self.num_models_agreeing,
            'num_models_total': self.num_models_total,
            'confidence_mean': self.confidence_mean,
            'confidence_std': self.confidence_std,
            'confidence_min': self.confidence_min,
            'confidence_max': self.confidence_max,
            'confidence_spread': self.confidence_spread,
            'prediction_entropy': self.prediction_entropy,
            'probability_entropy': self.probability_entropy,
            'probability_variance': self.probability_variance,
            'probability_std': self.probability_std,
            'model_votes': self.model_votes,
            'models_agreeing': self.models_agreeing,
            'models_disagreeing': self.models_disagreeing,
            'ensemble_prob': self.ensemble_prob,
            'ensemble_method': self.ensemble_method,
            'calibration_status': self.calibration_status,
        }


def compute_entropy(probs: np.ndarray) -> float:
    """Compute Shannon entropy of probability distribution."""
    probs = np.clip(probs, 1e-10, 1.0)
    return float(-np.sum(probs * np.log2(probs)))


def compute_vote_entropy(labels: np.ndarray) -> float:
    """Compute entropy of discrete vote distribution."""
    if len(labels) == 0:
        return 0.0
    unique, counts = np.unique(labels, return_counts=True)
    probs = counts / len(labels)
    return compute_entropy(probs)


def analyze_model_agreement(
    q1: str,
    q2: str,
    paths: Optional[AppPaths] = None,
) -> AgreementDashboard:
    """Generate agreement dashboard for a question pair."""
    if paths is None:
        paths = get_app_paths()

    report = get_agreement_report(q1, q2, paths)

    valid_votes = [v for v in report.votes if v.error is None]
    if not valid_votes:
        return AgreementDashboard(
            agreement_percentage=0.0,
            unanimous=False,
            num_models_agreeing=0,
            num_models_total=0,
            confidence_mean=0.0,
            confidence_std=0.0,
            confidence_min=0.0,
            confidence_max=0.0,
            confidence_spread=0.0,
            prediction_entropy=0.0,
            probability_entropy=0.0,
            probability_variance=0.0,
            probability_std=0.0,
            model_votes=[],
            models_agreeing=[],
            models_disagreeing=[],
            ensemble_prob=0.5,
            ensemble_method="none",
            calibration_status={},
        )

    # Extract data
    probs = np.array([v.prob_duplicate for v in valid_votes])
    labels = np.array([v.predicted_label for v in valid_votes])
    confidences = np.array([v.confidence for v in valid_votes])

    # Agreement
    majority_label = report.majority_label
    models_agreeing = [v.model_name for v in valid_votes if v.predicted_label == majority_label]
    models_disagreeing = [v.model_name for v in valid_votes if v.predicted_label != majority_label]
    agreement_pct = len(models_agreeing) / len(valid_votes) if valid_votes else 0.0

    # Confidence stats
    conf_mean = float(confidences.mean())
    conf_std = float(confidences.std())
    conf_min = float(confidences.min())
    conf_max = float(confidences.max())
    conf_spread = conf_max - conf_min

    # Entropy
    pred_entropy = compute_vote_entropy(labels)
    prob_entropy = compute_entropy(probs)

    # Variance
    prob_var = float(probs.var())
    prob_std = float(probs.std())

    # Model votes detail
    model_votes = []
    for v in valid_votes:
        model_votes.append({
            'model': v.model_name,
            'vote': 'Duplicate' if v.predicted_label == 1 else 'Non-Duplicate',
            'prob_duplicate': v.prob_duplicate,
            'confidence': v.confidence,
            'threshold': v.threshold,
            'latency_ms': v.latency_ms,
        })

    # Calibration status (simplified)
    calibration_status = {}
    for v in valid_votes:
        # Simple heuristic: if confidence >> accuracy, overconfident
        # We don't have ground truth here, so use ensemble as proxy
        ensemble_agrees = (v.predicted_label == report.majority_label)
        if v.confidence > 0.9 and not ensemble_agrees:
            calibration_status[v.model_name] = "overconfident"
        elif v.confidence < 0.6 and ensemble_agrees:
            calibration_status[v.model_name] = "underconfident"
        else:
            calibration_status[v.model_name] = "calibrated"

    return AgreementDashboard(
        agreement_percentage=agreement_pct,
        unanimous=report.unanimous,
        num_models_agreeing=len(models_agreeing),
        num_models_total=len(valid_votes),
        confidence_mean=conf_mean,
        confidence_std=conf_std,
        confidence_min=conf_min,
        confidence_max=conf_max,
        confidence_spread=conf_spread,
        prediction_entropy=pred_entropy,
        probability_entropy=prob_entropy,
        probability_variance=prob_var,
        probability_std=prob_std,
        model_votes=model_votes,
        models_agreeing=models_agreeing,
        models_disagreeing=models_disagreeing,
        ensemble_prob=report.ensemble_prob,
        ensemble_method="trimmed_mean" if len(valid_votes) >= 4 else "mean",
        calibration_status=calibration_status,
    )


@dataclass
class ModelLeaderboard:
    """Ranked model leaderboard with multiple criteria."""
    by_accuracy: List[Tuple[str, float]]
    by_confidence: List[Tuple[str, float]]
    by_calibration: List[Tuple[str, float]]  # ECE (lower is better)
    by_agreement: List[Tuple[str, float]]    # Agreement with ensemble
    by_influence: List[Tuple[str, float]]    # Influence on ensemble
    by_speed: List[Tuple[str, float]]        # Latency (lower is better)

    def get_strongest_model(self) -> str:
        return self.by_accuracy[0][0] if self.by_accuracy else "N/A"

    def get_weakest_model(self) -> str:
        return self.by_accuracy[-1][0] if self.by_accuracy else "N/A"

    def get_most_influential(self) -> str:
        return self.by_influence[0][0] if self.by_influence else "N/A"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'by_accuracy': self.by_accuracy,
            'by_confidence': self.by_confidence,
            'by_calibration': self.by_calibration,
            'by_agreement': self.by_agreement,
            'by_influence': self.by_influence,
            'by_speed': self.by_speed,
            'strongest_model': self.get_strongest_model(),
            'weakest_model': self.get_weakest_model(),
            'most_influential': self.get_most_influential(),
        }


def compute_model_leaderboard(
    predictions: List[Dict[str, Any]],
    ground_truth: List[int],
) -> ModelLeaderboard:
    """Compute model leaderboard from a set of predictions.

    Args:
        predictions: List of prediction dicts with 'model_votes' or 'feature_breakdown'
        ground_truth: List of true labels (0 or 1)

    Returns:
        ModelLeaderboard with ranked models
    """
    # Aggregate per-model statistics
    model_stats = defaultdict(lambda: {
        'probs': [],
        'labels': [],
        'confidences': [],
        'latencies': [],
        'correct': 0,
        'total': 0,
        'agree_with_ensemble': 0,
    })

    for pred, true_label in zip(predictions, ground_truth):
        # Extract model votes
        votes = pred.get('feature_breakdown', {})
        ensemble_pred = pred.get('predicted_label', 0)

        for model_name, contrib in votes.items():
            if isinstance(contrib, dict):
                prob = contrib.get('prob_dup', contrib.get('prob_duplicate', 0.5))
                conf = contrib.get('confidence', max(prob, 1-prob))
            else:
                prob = float(contrib)
                conf = max(prob, 1-prob)

            model_label = 1 if prob >= 0.5 else 0
            stats = model_stats[model_name]
            stats['probs'].append(prob)
            stats['labels'].append(model_label)
            stats['confidences'].append(conf)
            stats['total'] += 1
            if model_label == true_label:
                stats['correct'] += 1
            if model_label == ensemble_pred:
                stats['agree_with_ensemble'] += 1

    # Compute rankings
    by_accuracy = []
    by_confidence = []
    by_calibration = []
    by_agreement = []
    by_influence = []
    by_speed = []

    for name, stats in model_stats.items():
        if stats['total'] == 0:
            continue

        acc = stats['correct'] / stats['total']
        avg_conf = np.mean(stats['confidences']) if stats['confidences'] else 0.0

        # ECE
        if stats['probs'] and stats['labels']:
            probs_arr = np.array(stats['probs'])
            labels_arr = np.array(stats['labels'])
            ece = compute_ece(probs_arr, labels_arr)
        else:
            ece = 1.0

        agree_rate = stats['agree_with_ensemble'] / stats['total'] if stats['total'] > 0 else 0.0
        influence = acc * agree_rate  # Combined metric
        avg_latency = np.mean(stats['latencies']) if stats['latencies'] else 1000.0

        by_accuracy.append((name, acc))
        by_confidence.append((name, avg_conf))
        by_calibration.append((name, ece))
        by_agreement.append((name, agree_rate))
        by_influence.append((name, influence))
        by_speed.append((name, avg_latency))

    # Sort (accuracy, confidence, agreement, influence descending; calibration, speed ascending)
    by_accuracy.sort(key=lambda x: x[1], reverse=True)
    by_confidence.sort(key=lambda x: x[1], reverse=True)
    by_calibration.sort(key=lambda x: x[1])  # Lower ECE is better
    by_agreement.sort(key=lambda x: x[1], reverse=True)
    by_influence.sort(key=lambda x: x[1], reverse=True)
    by_speed.sort(key=lambda x: x[1])  # Lower latency is better

    return ModelLeaderboard(
        by_accuracy=by_accuracy,
        by_confidence=by_confidence,
        by_calibration=by_calibration,
        by_agreement=by_agreement,
        by_influence=by_influence,
        by_speed=by_speed,
    )


def compute_ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error."""
    if len(probs) == 0:
        return 1.0

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

    return float(ece / len(probs)) if len(probs) > 0 else 1.0


def generate_agreement_summary(
    q1: str,
    q2: str,
    paths: Optional[AppPaths] = None,
) -> Dict[str, Any]:
    """Generate human-readable agreement summary."""
    dashboard = analyze_model_agreement(q1, q2, paths)

    summary = {
        'overall': f"{dashboard.num_models_agreeing}/{dashboard.num_models_total} models agree ({dashboard.agreement_percentage:.0%})",
        'confidence': f"Mean: {dashboard.confidence_mean:.1%}, Spread: {dashboard.confidence_spread:.1%}",
        'entropy': f"Prediction entropy: {dashboard.prediction_entropy:.3f}, Probability entropy: {dashboard.probability_entropy:.3f}",
        'variance': f"Prob variance: {dashboard.probability_variance:.4f} (std: {dashboard.probability_std:.4f})",
        'disagreement': f"Models disagreeing: {', '.join(dashboard.models_disagreeing) if dashboard.models_disagreeing else 'None'}",
    }

    # Add interpretation
    if dashboard.agreement_percentage >= 0.9:
        summary['interpretation'] = "High consensus - prediction is reliable"
    elif dashboard.agreement_percentage >= 0.7:
        summary['interpretation'] = "Moderate consensus - prediction likely correct"
    elif dashboard.agreement_percentage >= 0.5:
        summary['interpretation'] = "Low consensus - prediction uncertain, consider human review"
    else:
        summary['interpretation'] = "High disagreement - prediction unreliable"

    if dashboard.confidence_spread > 0.5:
        summary['confidence_warning'] = "Large confidence spread among models"

    if dashboard.probability_std > 0.3:
        summary['variance_warning'] = "High probability variance - models strongly disagree on likelihood"

    return summary