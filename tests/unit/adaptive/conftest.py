from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from ares._result import PredictionResult
from ares.adaptive.config_loader import load_adaptive_config
from ares.adaptive.models import DifficultyAssessment, ModelEvidence


class FakeEngine:
    """Deterministic ``PredictionEngine`` stub for offline adaptive routing tests.

    Behaviours are keyed by exact model name and describe how each model should
    answer: ``(predicted_label, prob_duplicate, confidence, latency_ms)``.
    Addresses are recorded so tests can assert exactly which models ran
    (escalation / early-exit / budget behaviour).
    """

    def __init__(
        self,
        behaviors: dict[str, tuple[int, float, float, float]] | None = None,
        failures: set[str] | None = None,
        track: list[str] | None = None,
    ) -> None:
        self.behaviors: dict[str, tuple[int, float, float, float]] = behaviors or {}
        self.failures: set[str] = failures or set()
        self.track: list[str] = track if track is not None else []

    def predict(self, question1: str, question2: str, **kwargs: Any) -> PredictionResult:
        model = kwargs.get("model")
        self.track.append(model)
        if model in self.failures:
            from ares.orchestration.exceptions import TaskExecutionError

            raise TaskExecutionError(f"model {model} failed")
        label, prob, confidence, latency = self.behaviors.get(model, (0, 0.2, 0.6, 5.0))
        return PredictionResult(
            predicted_label=label,
            prediction="Duplicate" if label == 1 else "Non-Duplicate",
            confidence=confidence,
            prob_duplicate=prob,
            prob_non_duplicate=round(1.0 - prob, 6),
            model_name=model,
            latency_ms=latency,
            backend="fake",
            threshold=float(kwargs.get("threshold", 0.5)),
        )


def make_evidence(
    model_name: str,
    prob_duplicate: float,
    predicted_label: int,
    confidence: float,
    latency_ms: float = 1.0,
    strategy: str = "test",
    rank: int = 1,
) -> ModelEvidence:
    return ModelEvidence(
        model_name=model_name,
        prob_duplicate=prob_duplicate,
        predicted_label=predicted_label,
        prediction="Duplicate" if predicted_label == 1 else "Non-Duplicate",
        confidence=confidence,
        latency_ms=latency_ms,
        strategy=strategy,
        rank=rank,
    )


def make_assessment(
    difficulty_level: str = "easy",
    difficulty_score: float = 0.1,
    risk_level: str = "low",
    uncertainty_score: float = 0.1,
    **extra: Any,
) -> DifficultyAssessment:
    return DifficultyAssessment(
        difficulty_score=difficulty_score,
        difficulty_level=difficulty_level,
        uncertainty_score=uncertainty_score,
        risk_level=risk_level,
        **extra,
    )


@pytest.fixture
def default_config() -> dict[str, Any]:
    return load_adaptive_config()


@pytest.fixture
def engine_builder() -> Callable[..., FakeEngine]:
    return lambda **kw: FakeEngine(**kw)
