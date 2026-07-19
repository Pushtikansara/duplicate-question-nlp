"""Semantic Error Analysis — auto-categorizes prediction errors into types
(abbreviation, synonym, negation, entity mismatch, etc.)

Also performs Hard Negative Mining to identify false positives, false
negatives, borderline predictions, and hard examples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# Error categories for semantic analysis
@dataclass
class ErrorCategory:
    name: str
    description: str
    detected: bool = False
    confidence: float = 0.0
    details: str = ""


def categorize_error(
    q1: str,
    q2: str,
    predicted_label: int,
    true_label: int | None,
    prob_duplicate: float,
    all_model_probs: list[float] | None = None,
) -> list[ErrorCategory]:
    """Categorize a prediction error into specific types.

    Args:
        q1, q2: The two questions
        predicted_label: Model's prediction (0 or 1)
        true_label: Ground truth label if available (0, 1, or None)
        prob_duplicate: Predicted probability of duplicate
        all_model_probs: Probabilities from all models, for disagreement analysis

    Returns:
        List of ErrorCategory objects describing detected error types
    """
    q1_lower = q1.lower()
    q2_lower = q2.lower()
    errors: list[ErrorCategory] = []

    # Check if this is actually an error
    is_error = (true_label is not None and predicted_label != true_label)

    # 1. Abbreviation failure
    abbrevs_q1 = re.findall(r"\b[A-Z]{2,5}\b", q1)
    abbrevs_q2 = re.findall(r"\b[A-Z]{2,5}\b", q2)
    if abbrevs_q1 or abbrevs_q2:
        common = set(abbrevs_q1) & set(abbrevs_q2)
        if not common and (abbrevs_q1 or abbrevs_q2):
            errors.append(ErrorCategory(
                name="Abbreviation",
                description="Questions use abbreviations that may not match across models",
                detected=True,
                confidence=0.7,
                details=f"Q1 abbrevs: {abbrevs_q1[:3]}, Q2 abbrevs: {abbrevs_q2[:3]}",
            ))

    # 2. Synonym detection
    synonym_pairs = [
        ("learn", "study"), ("benefits", "advantages"),
        ("tutorial", "guide"), ("difference", "distinction"),
        ("explain", "what is"), ("how to", "way to"),
        ("meaning", "definition"), ("implement", "build"),
        ("train", "teach"), ("install", "setup"),
    ]
    syn_detected = []
    for w1, w2 in synonym_pairs:
        if (w1 in q1_lower and w2 in q2_lower) or (w2 in q1_lower and w1 in q2_lower):
            syn_detected.append(f"'{w1}'↔'{w2}'")
    if syn_detected:
        errors.append(ErrorCategory(
            name="Synonym",
            description="Questions use synonyms - requires semantic understanding",
            detected=True,
            confidence=0.8,
            details=", ".join(syn_detected),
        ))

    # 3. Negation
    negation_words = {"not", "no", "don't", "doesn't", "didn't", "won't", "can't", "isn't", "aren't"}
    neg_q1 = any(w in q1_lower.split() for w in negation_words)
    neg_q2 = any(w in q2_lower.split() for w in negation_words)
    if neg_q1 != neg_q2:
        errors.append(ErrorCategory(
            name="Negation",
            description="One question contains negation while the other doesn't",
            detected=True,
            confidence=0.9,
            details=f"Q1 negation: {neg_q1}, Q2 negation: {neg_q2}",
        ))

    # 4. Question type mismatch
    q_types = {
        "what": r"\bwhat\b", "how": r"\bhow\b", "why": r"\bwhy\b",
        "when": r"\bwhen\b", "where": r"\bwhere\b", "which": r"\bwhich\b",
        "who": r"\bwho\b", "explain": r"\bexplain\b", "define": r"\bdefine\b",
        "difference": r"\bdifference\b", "benefits": r"\bbenefits\b",
    }
    type_q1 = [name for name, pat in q_types.items() if re.search(pat, q1_lower)]
    type_q2 = [name for name, pat in q_types.items() if re.search(pat, q2_lower)]
    if type_q1 and type_q2 and set(type_q1) != set(type_q2):
        errors.append(ErrorCategory(
            name="Question Type Mismatch",
            description="Questions ask different types of questions",
            detected=True,
            confidence=0.6,
            details=f"Q1 type: {type_q1}, Q2 type: {type_q2}",
        ))

    # 5. Entity mismatch
    # Detect capitalized named entities
    entities_q1 = re.findall(r"\b[A-Z][a-z]+\b", q1)
    entities_q2 = re.findall(r"\b[A-Z][a-z]+\b", q2)
    if entities_q1 and entities_q2 and not set(entities_q1) & set(entities_q2):
        errors.append(ErrorCategory(
            name="Entity Mismatch",
            description="Questions reference different named entities",
            detected=True,
            confidence=0.7,
            details=f"Q1 entities: {entities_q1[:3]}, Q2 entities: {entities_q2[:3]}",
        ))

    # 6. Word order / paraphrase
    q1_words = set(q1_lower.split())
    q2_words = set(q2_lower.split())
    if len(q1_words & q2_words) / max(1, len(q1_words | q2_words)) > 0.5 and q1_lower != q2_lower:
        errors.append(ErrorCategory(
            name="Paraphrase / Word Order",
            description="High word overlap but different structure — likely paraphrases",
            detected=True,
            confidence=0.75,
            details=f"Word overlap: {len(q1_words & q2_words)}/{len(q1_words | q2_words)}",
        ))

    # 7. Borderline / uncertainty
    if abs(prob_duplicate - 0.5) < 0.15:
        errors.append(ErrorCategory(
            name="Borderline",
            description="Model is uncertain — probability near 0.5",
            detected=True,
            confidence=1.0 - 2.0 * abs(prob_duplicate - 0.5),
            details=f"Probability: {prob_duplicate:.4f}",
        ))

    # 8. Model disagreement (if multiple model probabilities available)
    if all_model_probs and len(all_model_probs) > 1:
        probs = np.array(all_model_probs)
        prob_std = float(probs.std())
        if prob_std > 0.3:
            errors.append(ErrorCategory(
                name="Model Disagreement",
                description="Models disagree strongly on this pair",
                detected=True,
                confidence=min(1.0, prob_std),
                details=f"Prob std: {prob_std:.3f} across {len(probs)} models",
            ))

    return errors if errors else [ErrorCategory(
        name="No Error Detected",
        description="No specific error pattern detected",
        detected=False,
        confidence=0.0,
        details="",
    )]


def classify_hardness(
    prob_duplicate: float,
    confidence: float,
    model_agreement: float,
    predicted_label: int,
    true_label: int | None = None,
) -> str:
    """Classify a prediction into hardness categories.

    Returns one of: 'easy', 'medium', 'hard', 'borderline', 'error'
    """
    if predicted_label != true_label:
        return "error"
    if abs(prob_duplicate - 0.5) < 0.15:
        return "borderline"
    if model_agreement < 0.6:
        return "hard"
    if confidence > 0.95:
        return "easy"
    return "medium"


def mine_hard_examples(
    predictions: list[dict[str, Any]],
    min_count: int = 10,
) -> dict[str, pd.DataFrame]:
    """Mine hard examples from a list of predictions.

    Returns separate DataFrames for:
    - false_positives: Predicted duplicate, actually non-duplicate
    - false_negatives: Predicted non-duplicate, actually duplicate
    - borderline: Prediction near 0.5 threshold
    - low_agreement: Models disagree strongly
    """
    fps, fns, borders, low_agreements = [], [], [], []

    for pred in predictions:
        prob = pred.get("prob_duplicate", 0.5)
        predicted = pred.get("predicted_label", 0)
        true_label = pred.get("true_label", None)
        model_agreement = pred.get("model_agreement", 1.0)
        confidence = pred.get("confidence", 0.0)

        # False positives
        if true_label is not None and predicted == 1 and true_label == 0:
            fps.append(pred)

        # False negatives
        if true_label is not None and predicted == 0 and true_label == 1:
            fns.append(pred)

        # Borderline
        if abs(prob - 0.5) < 0.15:
            borders.append(pred)

        # Low agreement
        if model_agreement < 0.6:
            low_agreements.append(pred)

    return {
        "false_positives": pd.DataFrame(fps[:min(min_count, len(fps))]) if fps else pd.DataFrame(),
        "false_negatives": pd.DataFrame(fns[:min(min_count, len(fns))]) if fns else pd.DataFrame(),
        "borderline": pd.DataFrame(borders[:min(min_count, len(borders))]) if borders else pd.DataFrame(),
        "low_agreement": pd.DataFrame(low_agreements[:min(min_count, len(low_agreements))]) if low_agreements else pd.DataFrame(),
    }


def generate_error_report(
    q1: str,
    q2: str,
    predicted_label: int,
    prob_duplicate: float,
    true_label: int | None = None,
    all_model_probs: list[float] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a comprehensive error analysis report for a single prediction."""
    errors = categorize_error(q1, q2, predicted_label, true_label, prob_duplicate, all_model_probs)

    hardness = classify_hardness(
        prob_duplicate,
        metadata.get("confidence", 0.0) if metadata else max(prob_duplicate, 1 - prob_duplicate),
        metadata.get("model_agreement", 1.0) if metadata else 1.0,
        predicted_label,
        true_label,
    )

    return {
        "q1": q1,
        "q2": q2,
        "predicted_label": predicted_label,
        "true_label": true_label,
        "prob_duplicate": prob_duplicate,
        "is_error": true_label is not None and predicted_label != true_label,
        "hardness": hardness,
        "error_categories": [
            {"name": e.name, "description": e.description,
             "detected": e.detected, "confidence": e.confidence, "details": e.details}
            for e in errors
        ],
        "metadata": metadata or {},
    }
