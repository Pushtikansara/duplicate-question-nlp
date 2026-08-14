from __future__ import annotations

from ares.adaptive.disagreement import DisagreementDetector
from ares.adaptive.models import DisagreementAssessment, ModelProfile

from .conftest import make_evidence


def detector(cfg=None, *, profiles=None):
    return DisagreementDetector(cfg, profile_registry=profiles)


class _Profiles:
    def __init__(self, profiles):
        self._profiles = profiles

    def get(self, model_name):
        return self._profiles.get(model_name)


def profile(model_name: str, accuracy: float, reliability: float, confidence_quality: float) -> ModelProfile:
    return ModelProfile(
        model_name=model_name,
        internal_id=model_name.lower(),
        model_type="transformer",
        capability_tier="transformer",
        expected_accuracy=accuracy,
        expected_latency_ms=5.0,
        computational_cost=5.0,
        memory_cost_mb=1.0,
        confidence_quality=confidence_quality,
        reliability=reliability,
        fallback_priority=1,
    )


class TestDisagreementDetection:
    def test_single_evidence_has_no_disagreement(self):
        a = detector().assess([make_evidence("A", 0.9, 1, 0.9)])
        assert a.disagreement_score == 0.0
        assert a.disagreement_level == "none"

    def test_agreement_scores_zero(self):
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.8, 1, 0.8),
        ]
        a = detector().assess(evs)
        assert a.disagreement_score < 0.25
        assert a.disagreement_level == "none"

    def test_split_labels_flag_disagreement(self):
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        a = detector().assess(evs)
        assert a.disagreement_score > 0.0
        assert a.evidence_count == 2

    def test_empty_evidences(self):
        a = detector().assess([])
        assert isinstance(a, DisagreementAssessment)
        assert a.evidence_count == 0


class TestResolutionStrategy:
    def test_default_is_confidence_weighted(self):
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        assert detector().assess(evs).resolution_strategy == "confidence_weighted"

    def test_explicit_majority_vote(self):
        cfg = {"fusion": {"method": "majority_vote"}}
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        a = detector(cfg).assess(evs)
        assert a.resolution_strategy == "majority_vote"
        assert a.resolution_label == 0  # tied -> non-duplicate

    def test_strongest_model_resolution(self):
        cfg = {"fusion": {"method": "strongest_model"}}
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        a = detector(cfg).assess(evs)
        assert a.resolution_label == 1  # model "A" wins on default accuracy

    def test_confidence_weighted_resolves_confident_model(self):
        evs = [
            make_evidence("A", 0.1, 0, 0.95),
            make_evidence("B", 0.97, 1, 0.97),
        ]
        a = detector().assess(evs)
        assert a.resolution_label == 1

    def test_explanation_records_evidence(self):
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        a = detector().assess(evs)
        assert "A" in a.explanation and "B" in a.explanation

    def test_invalid_strategy_falls_back(self):
        cfg = {"fusion": {"method": "unknown_strategy"}}
        evs = [make_evidence("A", 0.9, 1, 0.9), make_evidence("B", 0.1, 0, 0.9)]
        assert detector(cfg).assess(evs).resolution_strategy == "majority_vote"


class TestReliabilityAware:
    def test_confidence_weighting_uses_reliability(self):
        profiles = {"A": profile("A", 0.8, 0.9, 0.8), "B": profile("B", 0.8, 0.5, 0.8)}
        evs = [
            make_evidence("A", 0.1, 0, 0.95),
            make_evidence("B", 0.97, 1, 0.97),
        ]
        a = detector(profiles=_Profiles(profiles)).assess(evs)
        assert a.resolution_label == 0  # A is more reliable and wins

    def test_strongest_model_breaks_ties_by_reliability(self):
        cfg = {"fusion": {"method": "strongest_model"}}
        profiles = {
            "A": profile("A", 0.8, 0.5, 0.8),
            "B": profile("B", 0.8, 0.95, 0.8),
        }
        evs = [
            make_evidence("A", 0.9, 1, 0.9),
            make_evidence("B", 0.1, 0, 0.9),
        ]
        a = detector(cfg, profiles=_Profiles(profiles)).assess(evs)
        assert a.resolution_label == 0  # B wins on reliability, predicts non-duplicate


class TestDifficultyAware:
    def test_context_recorded(self):
        evs = [
            make_evidence("A", 0.9, 1, 0.95),
            make_evidence("B", 0.1, 0, 0.95),
        ]
        a = detector().assess(evs, difficulty_level="hard", risk_level="high")
        assert a.difficulty_level == "hard"
        assert a.risk_level == "high"

    def test_hard_difficulty_damps_confidence(self):
        profiles = {
            "A": profile("A", 0.999, 0.999, 0.999),
            "B": profile("B", 0.001, 0.001, 0.001),
        }
        evs = [
            make_evidence("A", 0.1, 0, 0.99),
            make_evidence("B", 0.97, 1, 0.97),
        ]
        # B is overconfident and unreliable; on hard requests its confidence is
        # damped so the reliable model A dominates.
        a = detector(profiles=_Profiles(profiles)).assess(evs, difficulty_level="hard")
        assert a.resolution_label == 0
