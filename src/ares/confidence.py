from __future__ import annotations

from typing import Any


def _get_single_weights(config: dict[str, Any] | None) -> dict[str, float]:
    raw_config = (config or {}).get("confidence", {}).get("single_model", {})
    return {
        "raw": float(raw_config.get("raw", 0.50)),
        "adjusted": float(raw_config.get("adjusted", 0.30)),
        "trust": float(raw_config.get("trust", 0.20)),
    }


def _get_multi_weights(config: dict[str, Any] | None) -> dict[str, float]:
    raw_config = (config or {}).get("confidence", {}).get("multi_model", {})
    return {
        "raw": float(raw_config.get("raw", 0.30)),
        "adjusted": float(raw_config.get("adjusted", 0.20)),
        "agreement": float(raw_config.get("agreement", 0.30)),
        "calibration": float(raw_config.get("calibration", 0.15)),
        "trust": float(raw_config.get("trust", 0.15)),
        "uncertainty_penalty": float(raw_config.get("uncertainty_penalty", 0.10)),
        "diversity_bonus": float(raw_config.get("diversity_bonus", 0.01)),
    }


def _get_trust_weights(config: dict[str, Any] | None) -> dict[str, float]:
    raw_config = (config or {}).get("trust", {})
    return {
        "confidence": float(raw_config.get("confidence_weight", 0.40)),
        "agreement": float(raw_config.get("agreement_weight", 0.20)),
        "contradiction": float(raw_config.get("contradiction_weight", 0.15)),
        "calibration": float(raw_config.get("calibration_weight", 0.15)),
        "uncertainty": float(raw_config.get("uncertainty_weight", 0.10)),
    }


def _get_trust_thresholds(config: dict[str, Any] | None) -> dict[str, float]:
    raw_config = (config or {}).get("trust_thresholds", {})
    return {
        "high": float(raw_config.get("high", 0.80)),
        "medium": float(raw_config.get("medium", 0.60)),
        "low": float(raw_config.get("low", 0.40)),
    }


def compute_final_confidence(
    raw_confidence: float,
    adjusted_confidence: float | None = None,
    agreement_score: float | None = None,
    calibration_score: float | None = None,
    trust_score: float | None = None,
    uncertainty: float | None = None,
    mode: str = "selected",
    model_count: int = 1,
) -> dict[str, Any]:
    if mode == "selected":
        return _single_model_confidence(raw_confidence, adjusted_confidence, trust_score)
    return _multi_model_confidence(
        raw_confidence,
        adjusted_confidence,
        agreement_score,
        calibration_score,
        trust_score,
        uncertainty,
        model_count,
    )


def _single_model_confidence(raw: float, adjusted: float | None, trust: float | None) -> dict[str, Any]:
    from ares._config import get_config

    config = get_config("inference")
    w = _get_single_weights(config)

    adj = adjusted if adjusted is not None else raw
    tr = trust if trust is not None else 0.5

    final = w["raw"] * raw + w["adjusted"] * adj + w["trust"] * tr
    final = max(0.05, min(0.99, final))

    return {
        "raw_confidence": raw,
        "adjusted_confidence": adj,
        "trust_score": tr,
        "final_confidence": final,
        "weights_used": w,
        "mode": "selected",
    }


def _multi_model_confidence(
    raw: float,
    adjusted: float | None,
    agreement: float | None,
    calibration: float | None,
    trust: float | None,
    uncertainty: float | None,
    model_count: int,
) -> dict[str, Any]:
    from ares._config import get_config

    config = get_config("inference")
    w = _get_multi_weights(config)

    adj = adjusted if adjusted is not None else raw
    ag = agreement if agreement is not None else 0.5
    ca = calibration if calibration is not None else 0.5
    tr = trust if trust is not None else 0.5
    uc = uncertainty if uncertainty is not None else 0.0

    final = (
        w["raw"] * raw
        + w["adjusted"] * adj
        + w["agreement"] * ag
        + w["calibration"] * ca
        + w["trust"] * tr
        - w["uncertainty_penalty"] * uc
        + w["diversity_bonus"] * min(5, model_count)
    )
    final = max(0.05, min(0.99, final))

    return {
        "raw_confidence": raw,
        "adjusted_confidence": adj,
        "agreement_score": ag,
        "calibration_score": ca,
        "trust_score": tr,
        "uncertainty": uc,
        "model_count": model_count,
        "final_confidence": final,
        "weights_used": w,
        "mode": "fusion",
    }


def compute_trust_score(
    confidence: float,
    agreement: float | None = None,
    contradiction_count: int = 0,
    calibration_error: float | None = None,
    uncertainty: float | None = None,
) -> float:
    from ares._config import get_config

    config = get_config("inference")
    w = _get_trust_weights(config)

    base = confidence * w["confidence"]

    ag = (agreement if agreement is not None else 0.5) * w["agreement"]

    contradiction_penalty = min(0.2, contradiction_count * 0.1)
    contradiction_factor = (1.0 - contradiction_penalty) * w["contradiction"]

    ce = (1.0 - (calibration_error if calibration_error is not None else 0.1)) * w["calibration"]

    uc = (1.0 - (uncertainty if uncertainty is not None else 0.2)) * w["uncertainty"]

    trust = base + ag + contradiction_factor + ce + uc
    return max(0.0, min(1.0, trust))


def compute_risk_level(
    trust_score: float,
    confidence: float | None = None,
    agreement: float | None = None,
    uncertainty: float | None = None,
    contradiction_count: int = 0,
) -> str:
    from ares._config import get_config

    config = get_config("inference")
    t = _get_trust_thresholds(config)

    penalties = 0.0
    if agreement is not None and agreement < 0.6:
        penalties += 0.15
    if uncertainty is not None and uncertainty > 0.3:
        penalties += 0.15
    if contradiction_count > 0:
        penalties += min(0.2, contradiction_count * 0.1)
    if confidence is not None and confidence < 0.5:
        penalties += 0.1

    effective_trust = max(0.0, trust_score - penalties)

    if effective_trust >= t["high"]:
        return "LOW"
    if effective_trust >= t["medium"]:
        return "MEDIUM"
    if effective_trust >= t["low"]:
        return "HIGH"
    return "CRITICAL"


def compute_trust_level(trust_score: float) -> str:
    from ares._config import get_config

    config = get_config("inference")
    t = _get_trust_thresholds(config)

    if trust_score >= t["high"]:
        return "HIGH"
    if trust_score >= t["medium"]:
        return "MEDIUM"
    if trust_score >= t["low"]:
        return "LOW"
    return "CRITICAL"


def compute_calibration_score(
    confidence: float,
    accuracy: float | None = None,
    num_samples: int = 0,
) -> float:
    if accuracy is None:
        return 0.5
    if num_samples < 10:
        return 0.5
    calibration_error = abs(confidence - accuracy)
    return max(0.0, 1.0 - calibration_error * 2.0)


def generate_explanation(
    prediction: str,
    confidence: float,
    model_name: str,
    question1: str,
    question2: str,
    agreement: float | None = None,
    uncertainty: float | None = None,
    trust_score: float | None = None,
    risk_level: str | None = None,
    semantic_penalty: float | None = None,
    model_contributions: dict[str, Any] | None = None,
    fusion_mode: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    if prediction == "Duplicate":
        if confidence >= 0.8:
            reasons.append(f"Both questions share strong semantic similarity ({confidence:.1%} confidence)")
        elif confidence >= 0.6:
            reasons.append(f"Questions appear semantically related ({confidence:.1%} confidence)")
        else:
            reasons.append(f"Model detected potential duplication ({confidence:.1%} confidence)")
    else:
        if confidence >= 0.8:
            reasons.append(f"Questions are semantically distinct ({confidence:.1%} confidence)")
        elif confidence >= 0.6:
            reasons.append(f"Questions likely address different topics ({confidence:.1%} confidence)")
        else:
            reasons.append(f"Model found insufficient evidence of duplication ({confidence:.1%} confidence)")

    if model_name:
        reasons.append(f"Primary model: {model_name}")

    if fusion_mode and model_contributions:
        agreeing = [
            m
            for m, d in model_contributions.items()
            if d.get("predicted_label") == (1 if prediction == "Duplicate" else 0)
        ]
        disagreeing = [
            m
            for m, d in model_contributions.items()
            if d.get("predicted_label") != (1 if prediction == "Duplicate" else 0)
        ]
        if agreeing:
            reasons.append(f"Models in agreement: {', '.join(agreeing[:3])}")
        if disagreeing:
            reasons.append(f"Models in disagreement: {', '.join(disagreeing[:3])}")

    if agreement is not None:
        if agreement >= 0.8:
            reasons.append("Strong model consensus")
        elif agreement < 0.6:
            reasons.append("Low model agreement — consider manual review")

    if uncertainty is not None and uncertainty > 0.3:
        reasons.append("High prediction uncertainty detected")

    if semantic_penalty is not None and semantic_penalty > 0:
        reasons.append(f"Semantic ambiguity detected (penalty: {semantic_penalty:.2f})")

    if trust_score is not None:
        if trust_score < 0.4:
            reasons.append("Low trust score — output should be verified")
        elif trust_score >= 0.8:
            reasons.append("High system trust in this prediction")

    if risk_level:
        reasons.append(f"Risk level: {risk_level}")

    return {
        "decision": prediction,
        "confidence": confidence,
        "model": model_name,
        "fusion": fusion_mode,
        "reasons": reasons,
        "summary": " ".join(reasons[:3]),
    }


def _consistent_reflection_from_confidence(confidence: float) -> dict[str, Any]:
    from ares._config import get_config

    config = get_config("inference")
    t = _get_trust_thresholds(config)

    if confidence >= t["high"]:
        trust_level = "HIGH"
        risk_level = "LOW"
        human_review = False
        recommendations: list[str] = []
    elif confidence >= t["medium"]:
        trust_level = "MEDIUM"
        risk_level = "MEDIUM"
        human_review = False
        recommendations = []
    elif confidence >= t["low"]:
        trust_level = "LOW"
        risk_level = "HIGH"
        human_review = True
        recommendations = ["review_manually"]
    else:
        trust_level = "LOW"
        risk_level = "HIGH"
        human_review = True
        recommendations = ["review_manually", "flag_for_expert_review"]

    return {
        "trust_score": confidence,
        "trust_level": trust_level,
        "risk_level": risk_level,
        "human_review_required": human_review,
        "recommendations": recommendations,
    }


def _ensure_consistent_reflection(reflection: dict[str, Any]) -> dict[str, Any]:
    trust_score = reflection.get("trust_score", 0.5)
    result = dict(reflection)
    consistent = _consistent_reflection_from_confidence(trust_score)
    result["trust_level"] = consistent["trust_level"]
    result["risk_level"] = consistent["risk_level"]
    result["human_review_required"] = consistent["human_review_required"]
    if not result.get("recommendations"):
        result["recommendations"] = consistent["recommendations"]
    return result
