from __future__ import annotations

from duplicate_question_app._reasoning.conflict_resolver import DefaultConflictResolver
from duplicate_question_app._reasoning.reasoning_result import (
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
)


class TestConflictResolver:
    def setup_method(self):
        self.resolver = DefaultConflictResolver()

    def test_no_conflicts(self):
        hyp = Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.8)
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
        conflicts = self.resolver.resolve([], [], [hyp], evidence)
        assert len(conflicts) == 0

    def test_identifies_conflicting_evidence(self):
        hyp = Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.8)
        evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.8,
                weight=1.0,
            ),
            Evidence(
                id="e2",
                hypothesis_id="h1",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.8,
                weight=1.0,
            ),
        ]
        conflicts = self.resolver.resolve([], [], [hyp], evidence)
        assert len(conflicts) >= 1
        assert conflicts[0].evidence_type == EvidenceType.CONTRADICTING

    def test_identifies_unsupported_hypotheses(self):
        hyp = Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.8)
        conflicts = self.resolver.resolve([], [], [hyp], [])
        assert len(conflicts) >= 1
        assert "no supporting evidence" in conflicts[0].text.lower()
