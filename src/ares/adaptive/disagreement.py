from __future__ import annotations

import statistics
from typing import Any

from ares.adaptive.models import DisagreementAssessment, ModelEvidence
from ares.adaptive.profiles import ModelProfileRegistry

RESOLUTION_STRATEGIES = ("majority_vote", "confidence_weighted", "strongest_model")


class DisagreementDetector:
    """Detects disagreement across multiple model predictions and resolves it
    using an explicit, configurable strategy.

    Probabilities are never blindly averaged: the resolution strategy is
    recorded on every assessment.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        profile_registry: ModelProfileRegistry | None = None,
    ) -> None:
        self._profile_registry = profile_registry
        self._config = config or {}

    def assess(
        self,
        evidences: list[ModelEvidence],
        *,
        difficulty_level: str | None = None,
        risk_level: str | None = None,
    ) -> DisagreementAssessment:
        count = len(evidences)
        if count == 0:
            return DisagreementAssessment(evidence_count=0)
        labels = [e.predicted_label for e in evidences]
        probabilities = [e.prob_duplicate for e in evidences]

        disagreement_score = self._disagreement_score(labels, probabilities)
        level = self._level(disagreement_score)

        strategy = str(self._config.get("fusion", {}).get("method", "confidence_weighted"))
        if strategy not in RESOLUTION_STRATEGIES:
            strategy = "majority_vote"
        resolution_label, resolution_prob = self._resolve(evidences, strategy, difficulty_level)

        joined = ", ".join(f"{e.model_name}={e.prob_duplicate:.2f}" for e in evidences)
        return DisagreementAssessment(
            disagreement_score=round(disagreement_score, 4),
            disagreement_level=level,
            labels=labels,
            probabilities=[round(p, 4) for p in probabilities],
            resolution_strategy=strategy,
            resolution_label=resolution_label,
            resolution_probability=round(resolution_prob, 4),
            explanation=f"{strategy} over [{joined}]",
            evidence_count=count,
            difficulty_level=difficulty_level,
            risk_level=risk_level,
        )

    @staticmethod
    def _disagreement_score(labels: list[int], probabilities: list[float]) -> float:
        n = len(labels)
        if n < 2:
            return 0.0
        # Normalised standard deviation of duplicate-probability spreads.
        std = statistics.stdev(probabilities) if n > 1 else 0.0
        normalized = min(1.0, std / 0.5)
        # Label entropy component: 1 = perfectly split, 0 = unanimous.
        dup_count = sum(labels)
        majority = max(dup_count, n - dup_count)
        label_agreement = majority / n
        return 0.6 * normalized + 0.4 * (1.0 - label_agreement)

    @staticmethod
    def _level(score: float) -> str:
        if score < 0.25:
            return "none"
        if score < 0.5:
            return "moderate"
        return "high"

    def _resolve(
        self,
        evidences: list[ModelEvidence],
        strategy: str,
        difficulty_level: str | None = None,
    ) -> tuple[int, float]:
        if strategy == "confidence_weighted":
            return self._confidence_weighted(evidences, difficulty_level)
        if strategy == "strongest_model":
            return self._strongest_model(evidences)
        return self._majority_vote(evidences)

    @staticmethod
    def _majority_vote(evidences: list[ModelEvidence]) -> tuple[int, float]:
        labels = [e.predicted_label for e in evidences]
        ones = sum(labels)
        zeros = len(labels) - ones
        label = 1 if ones > zeros else 0
        agreeing = [e for e in evidences if e.predicted_label == label]
        probability = statistics.mean([e.prob_duplicate for e in agreeing]) if agreeing else (1.0 if label else 0.0)
        return label, probability

    def _confidence_weighted(
        self, evidences: list[ModelEvidence], difficulty_level: str | None = None
    ) -> tuple[int, float]:
        hard = difficulty_level in ("hard", "critical")
        total_weight = 0.0
        weighted = 0.0
        for evidence in evidences:
            quality = self._quality_weight(evidence.model_name)
            reliability = self._reliability(evidence.model_name)
            confidence = max(0.1, evidence.confidence)
            # On hard/critical requests raw confidence is less trustworthy, so
            # the exponent damps it and the profile's reliability/quality
            # carry proportionally more of the resolution weight.
            weight = quality * reliability * (confidence**0.5 if hard else confidence)
            total_weight += weight
            weighted += evidence.prob_duplicate * weight
        probability = weighted / total_weight if total_weight > 0 else 0.5
        label = 1 if probability >= 0.5 else 0
        return label, probability

    def _strongest_model(self, evidences: list[ModelEvidence]) -> tuple[int, float]:
        best = None
        best_key = (-1.0, -1.0)
        for evidence in evidences:
            accuracy = self._accuracy(evidence.model_name)
            reliability = self._reliability(evidence.model_name)
            key = (accuracy, reliability)
            if key > best_key:
                best = evidence
                best_key = key
        if best is None:
            best = evidences[0]
        return best.predicted_label, best.prob_duplicate

    def _quality_weight(self, model_name: str) -> float:
        profile = self._profile_registry.get(model_name) if self._profile_registry else None
        if profile is None:
            return 1.0
        return profile.confidence_quality

    def _reliability(self, model_name: str) -> float:
        profile = self._profile_registry.get(model_name) if self._profile_registry else None
        if profile is None:
            return 1.0
        return profile.reliability

    def _accuracy(self, model_name: str) -> float:
        profile = self._profile_registry.get(model_name) if self._profile_registry else None
        if profile is None:
            return 0.5
        return profile.expected_accuracy
