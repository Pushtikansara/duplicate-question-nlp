from __future__ import annotations

from duplicate_question_app._reasoning.confidence_reasoner import DefaultConfidenceReasoner
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
)


class TestConfidenceReasoner:
    def setup_method(self):
        self.reasoner = DefaultConfidenceReasoner()

    def test_high_confidence_propagation(self):
        premises = [Premise(id="p1", text="p", source="t", category="c", confidence=0.95)]
        hypotheses = [Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.9)]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.9,
                weight=1.0,
            ),
        ]
        confidence = self.reasoner.propagate(premises, hypotheses, evidence)
        assert confidence > 0.5

    def test_low_confidence_propagation(self):
        premises = [Premise(id="p1", text="p", source="t", category="c", confidence=0.3)]
        hypotheses = [Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.2)]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.3,
                weight=1.0,
            ),
        ]
        confidence = self.reasoner.propagate(premises, hypotheses, evidence)
        assert confidence < 0.5

    def test_confidence_chain(self):
        premises = [Premise(id="p1", text="p", source="t", category="c", confidence=0.9)]
        hypotheses = [Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.8)]
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.85,
                weight=1.0,
            ),
        ]
        chain = self.reasoner.build_chain(premises, hypotheses, evidence, 0.85)
        assert chain.premise_confidence > 0
        assert chain.hypothesis_confidence > 0
        assert chain.evidence_confidence > 0
        assert chain.reasoning_confidence > 0
        assert chain.decision_confidence > 0
        assert "weighted_support" in chain.sources
        assert "weighted_contra" in chain.sources

    def test_empty_inputs(self):
        confidence = self.reasoner.propagate([], [], [])
        assert 0 <= confidence <= 1
