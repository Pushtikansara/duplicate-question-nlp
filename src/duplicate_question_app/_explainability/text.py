"""Advanced Explainability — generates plain English explanations for predictions.

Provides human-readable reasoning like:
"Prediction: Non-Duplicate
Reason: Different programming languages detected (Python vs JavaScript),
        Different intent (Installation vs Definition),
        Low lexical overlap (12%),
        Cross-encoder confidence low (0.31),
        Embedding similarity high (0.78) but overridden by penalties."
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from duplicate_question_app.agreement_dashboard import analyze_model_agreement
from duplicate_question_app.config import AppPaths, get_app_paths
from duplicate_question_app.contradiction_detector import get_contradiction_penalty
from duplicate_question_app.entity_detector import analyze_entity_mismatch
from duplicate_question_app.intent_detector import get_intent_details
from duplicate_question_app.lexical_penalty import get_lexical_penalty
from duplicate_question_app.negation_detector import get_negation_penalty


class ExplanationLevel(Enum):
    SIMPLE = "simple"  # One sentence
    DETAILED = "detailed"  # Bullet points with reasons
    TECHNICAL = "technical"  # Full technical breakdown
    DEBUG = "debug"  # Everything including raw scores


@dataclass
class ExplanationResult:
    """Complete explanation for a prediction."""

    prediction: str
    confidence: float
    probability: float
    level: ExplanationLevel
    summary: str
    reasons: list[str]
    details: dict[str, Any]

    def to_text(self) -> str:
        """Format as readable text."""
        lines = [
            f"Prediction: {self.prediction}",
            f"Confidence: {self.confidence:.1%}",
            f"Probability: {self.probability:.2%}",
            "",
            f"Summary: {self.summary}",
            "",
            "Reasons:",
        ]
        for i, reason in enumerate(self.reasons, 1):
            lines.append(f"  {i}. {reason}")

        if self.level in (ExplanationLevel.TECHNICAL, ExplanationLevel.DEBUG):
            lines.append("")
            lines.append("Technical Details:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "probability": self.probability,
            "level": self.level.value,
            "summary": self.summary,
            "reasons": self.reasons,
            "details": self.details,
        }


def generate_explanation(
    q1: str,
    q2: str,
    prediction_result: dict[str, Any],
    level: ExplanationLevel = ExplanationLevel.DETAILED,
    paths: AppPaths | None = None,
) -> ExplanationResult:
    """Generate plain English explanation for a prediction."""
    if paths is None:
        paths = get_app_paths()

    # Extract prediction info
    prediction = prediction_result.get("prediction", "Unknown")
    probability = prediction_result.get("prob_duplicate", 0.5)
    confidence = prediction_result.get("confidence", 0.5)

    # Gather all feature analyses
    entity_result = analyze_entity_mismatch(q1, q2)
    intent_details = get_intent_details(q1, q2)
    negation_penalty, negation_details = get_negation_penalty(q1, q2)
    contradiction_penalty, contradiction_details = get_contradiction_penalty(q1, q2)
    lexical_penalty, lexical_details = get_lexical_penalty(q1, q2)

    # Model agreement
    agreement = analyze_model_agreement(q1, q2, paths)

    # Build reasons
    reasons = []
    details = {}

    # 1. Entity mismatch
    if entity_result.mismatch_penalty > 0:
        entity_reasons = []
        for detail in entity_result.penalty_details:
            entity_reasons.append(detail)
        if entity_reasons:
            reasons.append(f"Entity mismatch: {'; '.join(entity_reasons)}")
        details["entity_penalty"] = entity_result.mismatch_penalty
        details["entity_details"] = entity_result.penalty_details

    # 2. Intent mismatch
    if intent_details["mismatch_penalty"] > 0:
        reasons.append(f"Intent mismatch: {intent_details['mismatch_reason']}")
        details["intent_penalty"] = intent_details["mismatch_penalty"]
        details["q1_intent"] = intent_details["q1_intent"]
        details["q2_intent"] = intent_details["q2_intent"]

    # 3. Negation
    if negation_penalty > 0:
        reasons.append(f"Negation mismatch: {negation_details}")
        details["negation_penalty"] = negation_penalty

    # 4. Contradiction
    if contradiction_penalty > 0:
        reasons.append(f"Contradiction detected: {contradiction_details}")
        details["contradiction_penalty"] = contradiction_penalty

    # 5. Lexical mismatch
    if lexical_penalty > 0:
        reasons.append(f"Lexical mismatch: {lexical_details}")
        details["lexical_penalty"] = lexical_penalty

    # 6. Model agreement
    if agreement.num_models_total > 0:
        agree_pct = agreement.agreement_percentage
        if agree_pct >= 0.9:
            reasons.append(f"High model agreement ({agree_pct:.0%} of models agree)")
        elif agree_pct >= 0.7:
            reasons.append(f"Moderate model agreement ({agree_pct:.0%} agree)")
        elif agree_pct >= 0.5:
            reasons.append(f"Low model agreement ({agree_pct:.0%} agree) - uncertain prediction")
        else:
            reasons.append(f"High model disagreement ({agree_pct:.0%} agree) - unreliable")

        if agreement.confidence_spread > 0.4:
            reasons.append(f"Large confidence spread among models ({agreement.confidence_spread:.1%})")

        if agreement.probability_std > 0.25:
            reasons.append(f"High probability variance (std={agreement.probability_std:.2f})")

    details["model_agreement"] = agreement.agreement_percentage
    details["confidence_spread"] = agreement.confidence_spread
    details["prob_std"] = agreement.probability_std

    # 7. Cross-encoder vs embedding divergence
    feature_breakdown = prediction_result.get("feature_breakdown", {})
    if feature_breakdown:
        # Check for cross-encoder
        cross_encoder_prob = None
        embedding_probs = []

        for model_name, contrib in feature_breakdown.items():
            if isinstance(contrib, dict):
                prob = contrib.get("prob_dup", contrib.get("prob_duplicate", 0.5))
                if "DeBERTa" in model_name or "Cross" in model_name:
                    cross_encoder_prob = prob
                elif any(x in model_name for x in ["BGE", "E5", "MPNet"]):
                    embedding_probs.append(prob)

        if cross_encoder_prob is not None and embedding_probs:
            avg_embedding = sum(embedding_probs) / len(embedding_probs)
            if avg_embedding > 0.7 and cross_encoder_prob < 0.4:
                reasons.append(
                    f"Embedding models suggest duplicate ({avg_embedding:.0%}) "
                    f"but cross-encoder disagrees ({cross_encoder_prob:.0%}) - "
                    "cross-encoder prioritized for accuracy"
                )
            elif avg_embedding < 0.4 and cross_encoder_prob > 0.7:
                reasons.append(
                    f"Cross-encoder suggests duplicate ({cross_encoder_prob:.0%}) "
                    f"but embeddings disagree ({avg_embedding:.0%})"
                )

            details["cross_encoder_prob"] = cross_encoder_prob
            details["avg_embedding_prob"] = avg_embedding

    # 8. Adaptive weights
    adaptive_weights = prediction_result.get("adaptive_weights", {})
    if adaptive_weights:
        weight_str = ", ".join(f"{k}={v:.0%}" for k, v in adaptive_weights.items())
        reasons.append(f"Dynamic ensemble weights: {weight_str}")
        details["adaptive_weights"] = adaptive_weights

    # 9. Specific false positive patterns
    q1_lower = q1.lower()
    q2_lower = q2.lower()

    # Programming language mismatch
    langs_q1 = {
        lang
        for lang in ["python", "java", "javascript", "c++", "c#", "go", "rust", "swift", "kotlin"]
        if lang in q1_lower
    }
    langs_q2 = {
        lang
        for lang in ["python", "java", "javascript", "c++", "c#", "go", "rust", "swift", "kotlin"]
        if lang in q2_lower
    }

    if langs_q1 and langs_q2 and langs_q1 != langs_q2:
        reasons.append(f"Different programming languages: {', '.join(langs_q1)} vs {', '.join(langs_q2)}")
        details["language_mismatch"] = {"q1": list(langs_q1), "q2": list(langs_q2)}

    # OS mismatch
    os_q1 = {os for os in ["windows", "linux", "ubuntu", "macos", "mac os", "android", "ios"] if os in q1_lower}
    os_q2 = {os for os in ["windows", "linux", "ubuntu", "macos", "mac os", "android", "ios"] if os in q2_lower}

    if os_q1 and os_q2 and os_q1 != os_q2:
        reasons.append(f"Different operating systems: {', '.join(os_q1)} vs {', '.join(os_q2)}")
        details["os_mismatch"] = {"q1": list(os_q1), "q2": list(os_q2)}

    # Software/framework mismatch
    sw_q1 = {
        sw
        for sw in [
            "docker",
            "kubernetes",
            "git",
            "github",
            "gitlab",
            "tensorflow",
            "pytorch",
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "spring",
        ]
        if sw in q1_lower
    }
    sw_q2 = {
        sw
        for sw in [
            "docker",
            "kubernetes",
            "git",
            "github",
            "gitlab",
            "tensorflow",
            "pytorch",
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "spring",
        ]
        if sw in q2_lower
    }

    if sw_q1 and sw_q2 and sw_q1 != sw_q2:
        reasons.append(f"Different technologies: {', '.join(sw_q1)} vs {', '.join(sw_q2)}")
        details["software_mismatch"] = {"q1": list(sw_q1), "q2": list(sw_q2)}

    # Generate summary
    if prediction == "Duplicate":
        if confidence > 0.9:
            summary = "Strong duplicate match - questions are semantically equivalent with high confidence"
        elif confidence > 0.7:
            summary = "Likely duplicate - questions share similar intent and content"
        else:
            summary = "Possible duplicate - some similarity but uncertain"
    else:
        if confidence > 0.9:
            summary = "Strong non-duplicate - questions are clearly different"
        elif confidence > 0.7:
            summary = "Likely different - key differences detected"
        else:
            summary = "Uncertain - questions have mixed signals"

    if not reasons:
        reasons.append("No significant mismatch patterns detected")

    return ExplanationResult(
        prediction=prediction,
        confidence=confidence,
        probability=probability,
        level=level,
        summary=summary,
        reasons=reasons,
        details=details,
    )


def generate_counterfactual_explanation(
    q1: str,
    q2: str,
    prediction_result: dict[str, Any],
    paths: AppPaths | None = None,
) -> dict[str, Any]:
    """Generate counterfactual: what would need to change for opposite prediction."""
    if paths is None:
        paths = get_app_paths()

    current_pred = prediction_result.get("prediction", "Non-Duplicate")
    current_prob = prediction_result.get("prob_duplicate", 0.5)

    target_pred = "Non-Duplicate" if current_pred == "Duplicate" else "Duplicate"
    1.0 - current_prob  # Rough target

    changes = []

    # Check each penalty source
    entity_result = analyze_entity_mismatch(q1, q2)
    if entity_result.mismatch_penalty > 0.2:
        changes.append(
            {
                "factor": "entities",
                "current": "Mismatched entities",
                "action": "Align key entities (languages, frameworks, products)",
                "impact": "high",
            }
        )

    intent_details = get_intent_details(q1, q2)
    if intent_details["mismatch_penalty"] > 0.2:
        changes.append(
            {
                "factor": "intent",
                "current": f"Different intents ({intent_details['q1_intent']} vs {intent_details['q2_intent']})",
                "action": "Make both questions ask the same type of question",
                "impact": "high",
            }
        )

    negation_penalty, _ = get_negation_penalty(q1, q2)
    if negation_penalty > 0.3:
        changes.append(
            {
                "factor": "negation",
                "current": "Negation mismatch",
                "action": "Ensure both questions have same negation polarity",
                "impact": "high",
            }
        )

    lexical_penalty, _ = get_lexical_penalty(q1, q2)
    if lexical_penalty > 0.3:
        changes.append(
            {
                "factor": "lexical",
                "current": "Low lexical overlap",
                "action": "Increase word overlap or use more similar phrasing",
                "impact": "medium",
            }
        )

    return {
        "current_prediction": current_pred,
        "current_probability": current_prob,
        "target_prediction": target_pred,
        "required_changes": changes,
        "difficulty": "easy" if len(changes) <= 1 else ("medium" if len(changes) <= 3 else "hard"),
    }


def generate_feature_importance(
    prediction_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate feature importance from prediction breakdown."""
    feature_breakdown = prediction_result.get("feature_breakdown", {})
    adaptive_weights = prediction_result.get("adaptive_weights", {})

    importances = []

    for model_name, contrib in feature_breakdown.items():
        if isinstance(contrib, dict):
            prob = contrib.get("prob_dup", contrib.get("prob_duplicate", 0.5))
            weight = contrib.get("weight", adaptive_weights.get(model_name, 0))
            weighted_contrib = contrib.get("weighted_contribution", prob * weight)
        else:
            prob = float(contrib)
            weight = adaptive_weights.get(model_name, 0)
            weighted_contrib = prob * weight

        importances.append(
            {
                "model": model_name,
                "raw_probability": prob,
                "weight": weight,
                "weighted_contribution": weighted_contrib,
                "vote": "Duplicate" if prob >= 0.5 else "Non-Duplicate",
            }
        )

    # Sort by absolute weighted contribution
    importances.sort(key=lambda x: abs(x["weighted_contribution"]), reverse=True)

    return importances
