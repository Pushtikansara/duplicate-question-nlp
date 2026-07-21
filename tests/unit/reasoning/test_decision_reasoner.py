from __future__ import annotations

from duplicate_question_app._reasoning.decision_reasoner import DefaultDecisionReasoner
from duplicate_question_app._reasoning.reasoning_result import Evidence, EvidenceType, Hypothesis, HypothesisLabel


class TestDecisionReasoner:
    def setup_method(self):
        self.reasoner = DefaultDecisionReasoner()

    def test_duplicate_decision(self):
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
                confidence=0.8,
                weight=1.0,
            ),
        ]
        decision = self.reasoner.decide(hypotheses, evidence, confidence=0.8, uncertainty=0.2)
        assert decision == "duplicate"

    def test_not_duplicate_decision(self):
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.2),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.8),
        ]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h2",
                evidence_type=EvidenceType.SUPPORTING,
                text="support non-dup",
                confidence=0.8,
                weight=1.0,
            ),
        ]
        decision = self.reasoner.decide(hypotheses, evidence, confidence=0.2, uncertainty=0.3)
        assert decision == "not_duplicate"

    def test_uncertain_when_high_uncertainty(self):
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.7),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.3),
        ]
        evidence = []
        decision = self.reasoner.decide(hypotheses, evidence, confidence=0.5, uncertainty=0.8)
        assert decision == "uncertain"

    def test_uncertain_when_tie(self):
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.51),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.49),
        ]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.5,
                weight=0.5,
            ),
            Evidence(
                id="e2",
                hypothesis_id="h2",
                evidence_type=EvidenceType.SUPPORTING,
                text="support2",
                confidence=0.5,
                weight=0.5,
            ),
        ]
        decision = self.reasoner.decide(hypotheses, evidence, confidence=0.5, uncertainty=0.55)
        assert decision == "uncertain"

    def test_cross_encoder_influences_decision(self):
        hypotheses = [
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.6),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.4),
        ]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.6,
                weight=0.5,
            ),
        ]
        decision = self.reasoner.decide(hypotheses, evidence, confidence=0.5, uncertainty=0.3, cross_encoder_score=0.9)
        assert decision == "duplicate"

    def test_build_reason_returns_string(self):
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="test evidence",
                confidence=0.8,
                weight=1.0,
            ),
        ]
        reason = self.reasoner.build_reason("duplicate", 0.8, 0.2, evidence)
        assert isinstance(reason, str)
        assert "duplicate" in reason.lower()
        assert "test evidence" in reason
