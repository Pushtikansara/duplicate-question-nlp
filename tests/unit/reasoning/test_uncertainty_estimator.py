from __future__ import annotations

from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
)
from duplicate_question_app._reasoning.uncertainty_estimator import DefaultUncertaintyEstimator


class TestUncertaintyEstimator:
    def setup_method(self):
        self.estimator = DefaultUncertaintyEstimator()

    def test_high_confidence_low_uncertainty(self):
        premises = [Premise(id="p1", text="p", source="t", category="c", confidence=0.95)]
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.85),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.15),
        ]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.9,
                weight=1.0,
            )
        ]
        uncertainty = self.estimator.estimate(premises, hypotheses, evidence, [])
        assert 0.0 <= uncertainty < 0.5

    def test_conflicting_evidence_high_uncertainty(self):
        premises = [Premise(id="p1", text="p", source="t", category="c", confidence=0.5)]
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.5),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.5),
        ]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.5,
                weight=0.5,
            )
        ]
        conflicts = [
            Evidence(
                id="c1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.5,
                weight=0.5,
            )
        ]
        uncertainty = self.estimator.estimate(premises, hypotheses, evidence, conflicts)
        assert 0.0 <= uncertainty <= 1.0

    def test_empty_inputs(self):
        uncertainty = self.estimator.estimate([], [], [], [])
        assert 0.0 <= uncertainty <= 1.0

    def test_uncertainty_is_bounded(self):
        for _ in range(10):
            premises = [Premise(id="p1", text="p", source="t", category="c", confidence=i / 10) for i in range(5)]
            uncertainty = self.estimator.estimate(premises, [], [], [])
            assert 0.0 <= uncertainty <= 1.0
