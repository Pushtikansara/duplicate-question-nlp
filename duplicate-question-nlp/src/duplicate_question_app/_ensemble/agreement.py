"""Model Agreement Engine — collects predictions from all 9 models and
computes agreement, disagreement, majority vote, and confidence variance.

Every prediction is analyzed across all available models to provide
insights into model consensus and semantic reliability.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from duplicate_question_app.config import (
    AppPaths,
    MODEL_CHOICES,
    get_app_paths,
)
from duplicate_question_app.inference import (
    DuplicateQuestionInferenceService,
    load_model_and_tokenizer,
)
from duplicate_question_app.week2_inference import Week2InferenceService, check_week2_artifacts
from duplicate_question_app.embedding_models import predict_with_sentence_transformer


@dataclass
class ModelVote:
    """A single model's prediction on a question pair."""
    model_name: str
    predicted_label: int          # 0 = non-duplicate, 1 = duplicate
    prob_duplicate: float
    confidence: float
    threshold: float
    latency_ms: float
    error: str | None = None


@dataclass
class AgreementReport:
    """Full model agreement analysis for a single prediction."""
    question1: str
    question2: str
    votes: list[ModelVote]
    majority_label: int
    majority_ratio: float          # fraction of models agreeing with majority
    unanimous: bool
    agreement_score: float         # 0.0 (total disagreement) to 1.0 (unanimous)
    confidence_mean: float
    confidence_variance: float
    prob_mean: float
    prob_std: float
    num_models_voted: int
    num_models_available: int
    models_agreeing: list[str]
    models_disagreeing: list[str]
    is_borderline: bool            # True if mean prob is near 0.5
    predicted_label: int           # final prediction (majority vote)
    prediction: str                # "Duplicate" or "Non-Duplicate"
    ensemble_prob: float           # trimmed mean probability
    latency_ms: float


def collect_all_votes(
    q1: str,
    q2: str,
    paths: AppPaths,
) -> list[ModelVote]:
    """Collect predictions from every available model."""
    votes: list[ModelVote] = []

    # Week 2 models
    if all(check_week2_artifacts(paths).values()):
        w2 = Week2InferenceService(paths)
        for m in ["TF-IDF + Logistic Regression (Week 2)", "TF-IDF + Linear SVM (Week 2)"]:
            try:
                t0 = time.time()
                _, prob_dup = w2.predict_proba(q1, q2, m)
                lat = (time.time() - t0) * 1000
                confidence = max(prob_dup, 1.0 - prob_dup)
                votes.append(ModelVote(
                    model_name=m,
                    predicted_label=1 if prob_dup >= 0.5 else 0,
                    prob_duplicate=prob_dup,
                    confidence=confidence,
                    threshold=0.5,
                    latency_ms=lat,
                ))
            except Exception as e:
                votes.append(ModelVote(model_name=m, predicted_label=0, prob_duplicate=0.0,
                                       confidence=0.0, threshold=0.5, latency_ms=0.0, error=str(e)))

    # Week 3 / Week 4 transformer models
    for m in ["DistilBERT (Week 3)", "Improved DistilBERT (Week 4)"]:
        try:
            t0 = time.time()
            model, tok, meta = load_model_and_tokenizer(paths, model_version=m)
            svc = DuplicateQuestionInferenceService(model, tok, meta)
            _, prob_dup = svc.predict_proba(q1, q2)
            lat = (time.time() - t0) * 1000
            confidence = max(prob_dup, 1.0 - prob_dup)
            votes.append(ModelVote(
                model_name=m,
                predicted_label=1 if prob_dup >= meta.decision_threshold else 0,
                prob_duplicate=prob_dup,
                confidence=confidence,
                threshold=meta.decision_threshold,
                latency_ms=lat,
            ))
        except Exception as e:
            votes.append(ModelVote(model_name=m, predicted_label=0, prob_duplicate=0.0,
                                   confidence=0.0, threshold=0.5, latency_ms=0.0, error=str(e)))

    # Phase 2 embedding / cross-encoder models
    for m in ["BGE-base-en-v1.5", "E5-base-v2", "MPNet-base-v2", "DeBERTa-v3 Cross-Encoder"]:
        try:
            t0 = time.time()
            result = predict_with_sentence_transformer(m, q1, q2)
            lat = (time.time() - t0) * 1000
            prob_dup = result["prob_duplicate"]
            confidence = result["confidence"]
            votes.append(ModelVote(
                model_name=m,
                predicted_label=result["predicted_label"],
                prob_duplicate=prob_dup,
                confidence=confidence,
                threshold=result["threshold"],
                latency_ms=lat,
            ))
        except Exception as e:
            votes.append(ModelVote(model_name=m, predicted_label=0, prob_duplicate=0.0,
                                   confidence=0.0, threshold=0.5, latency_ms=0.0, error=str(e)))

    return votes


def analyze_agreement(votes: list[ModelVote], q1: str, q2: str) -> AgreementReport:
    """Analyze model agreement from collected votes."""
    valid_votes = [v for v in votes if v.error is None]
    if not valid_votes:
        return AgreementReport(
            question1=q1, question2=q2, votes=votes,
            majority_label=0, majority_ratio=0.0, unanimous=False,
            agreement_score=0.0, confidence_mean=0.0, confidence_variance=0.0,
            prob_mean=0.0, prob_std=0.0, num_models_voted=0,
            num_models_available=len(votes),
            models_agreeing=[], models_disagreeing=[],
            is_borderline=False, predicted_label=0, prediction="Non-Duplicate",
            ensemble_prob=0.0, latency_ms=0.0,
        )

    probs = np.array([v.prob_duplicate for v in valid_votes])
    labels = np.array([v.predicted_label for v in valid_votes])
    confs = np.array([v.confidence for v in valid_votes])
    latencies = np.array([v.latency_ms for v in valid_votes])

    # Majority vote
    n_dup = int(labels.sum())
    n_non = len(labels) - n_dup
    majority_label = 1 if n_dup > n_non else (0 if n_non > n_dup else 0)  # tie-break to non-dup
    majority_ratio = max(n_dup, n_non) / len(labels)
    unanimous = majority_ratio == 1.0

    # Models agreeing / disagreeing
    models_agreeing = [v.model_name for v in valid_votes if v.predicted_label == majority_label]
    models_disagreeing = [v.model_name for v in valid_votes if v.predicted_label != majority_label]

    # Agreement score: how many models agree (0-1)
    agreement_score = majority_ratio

    # Confidence statistics
    confidence_mean = float(confs.mean())
    confidence_variance = float(confs.var()) if len(confs) > 1 else 0.0

    # Probability statistics
    prob_mean = float(probs.mean())
    prob_std = float(probs.std()) if len(probs) > 1 else 0.0

    # Trimmed mean for ensemble (drop 1 highest, 1 lowest if >= 4 models)
    sorted_probs = sorted(probs)
    if len(sorted_probs) >= 4:
        trimmed = sorted_probs[1:-1]
    elif len(sorted_probs) >= 2:
        trimmed = sorted_probs
    else:
        trimmed = sorted_probs
    ensemble_prob = float(np.mean(trimmed))

    # Borderline detection (mean prob near 0.5)
    is_borderline = abs(prob_mean - 0.5) < 0.15

    return AgreementReport(
        question1=q1,
        question2=q2,
        votes=votes,
        majority_label=majority_label,
        majority_ratio=float(majority_ratio),
        unanimous=bool(unanimous),
        agreement_score=float(agreement_score),
        confidence_mean=confidence_mean,
        confidence_variance=confidence_variance,
        prob_mean=prob_mean,
        prob_std=prob_std,
        num_models_voted=len(valid_votes),
        num_models_available=len(votes),
        models_agreeing=models_agreeing,
        models_disagreeing=models_disagreeing,
        is_borderline=is_borderline,
        predicted_label=majority_label,
        prediction="Duplicate" if majority_label == 1 else "Non-Duplicate",
        ensemble_prob=ensemble_prob,
        latency_ms=float(latencies.sum()),
    )


def get_agreement_report(
    q1: str,
    q2: str,
    paths: AppPaths | None = None,
) -> AgreementReport:
    """Convenience function: collect votes and analyze agreement.

    This is the main entry point for the agreement engine.
    """
    if paths is None:
        from pathlib import Path
        paths = get_app_paths(Path(__file__).resolve().parents[2])
    votes = collect_all_votes(q1, q2, paths)
    return analyze_agreement(votes, q1, q2)


def agreement_to_dict(report: AgreementReport) -> dict[str, Any]:
    """Convert AgreementReport to a serializable dict for JSON/Streamlit display."""
    return {
        "question1": report.question1,
        "question2": report.question2,
        "majority_label": report.majority_label,
        "majority_ratio": report.majority_ratio,
        "prediction": report.prediction,
        "unanimous": report.unanimous,
        "agreement_score": report.agreement_score,
        "confidence_mean": report.confidence_mean,
        "confidence_variance": report.confidence_variance,
        "prob_mean": report.prob_mean,
        "prob_std": report.prob_std,
        "num_models_voted": report.num_models_voted,
        "num_models_available": report.num_models_available,
        "is_borderline": report.is_borderline,
        "ensemble_prob": report.ensemble_prob,
        "models_agreeing": report.models_agreeing,
        "models_disagreeing": report.models_disagreeing,
        "latency_ms": report.latency_ms,
        "votes": [
            {
                "model_name": v.model_name,
                "predicted_label": v.predicted_label,
                "prob_duplicate": v.prob_duplicate,
                "confidence": v.confidence,
                "threshold": v.threshold,
                "latency_ms": v.latency_ms,
                "error": v.error,
            }
            for v in report.votes
        ],
    }
