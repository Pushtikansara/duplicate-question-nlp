from __future__ import annotations

import logging

from ares.api.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_question_pair(question1: str, question2: str) -> None:
    errors: list[str] = []
    if not question1 or not question1.strip():
        errors.append("question1 must not be empty")
    if not question2 or not question2.strip():
        errors.append("question2 must not be empty")
    if len(question1) > 1000:
        errors.append("question1 exceeds maximum length of 1000 characters")
    if len(question2) > 1000:
        errors.append("question2 exceeds maximum length of 1000 characters")
    if question1.strip() == question2.strip():
        errors.append("questions must be different")
    if errors:
        raise ValidationError(detail="; ".join(errors))


def validate_model_name(model: str | None) -> str:
    if model is None:
        from ares.api.config import APIConfig

        return APIConfig.get().default_model
    valid_models = [
        "TF-IDF + Logistic Regression (Week 2)",
        "TF-IDF + Linear SVM (Week 2)",
        "DistilBERT (Week 3)",
        "Improved DistilBERT (Week 4)",
        "BGE-base-en-v1.5",
        "E5-base-v2",
        "E5-quora-finetuned",
        "MPNet-base-v2",
        "DeBERTa-v3 Cross-Encoder",
        "Cross-Encoder-Quora (Trained)",
        "Semantic Ensemble",
    ]
    if model not in valid_models:
        raise ValidationError(detail=f"Unknown model '{model}'. Valid models: {', '.join(valid_models)}")
    return model


def validate_threshold(threshold: float | None) -> float:
    if threshold is None:
        from ares.api.config import APIConfig

        return APIConfig.get().default_threshold
    if not 0.0 <= threshold <= 1.0:
        raise ValidationError(detail="Threshold must be between 0.0 and 1.0")
    return threshold
