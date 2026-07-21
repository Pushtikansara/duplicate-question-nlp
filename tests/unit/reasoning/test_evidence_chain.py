from __future__ import annotations

from duplicate_question_app._reasoning.evidence_chain import DefaultEvidenceChain
from duplicate_question_app._reasoning.reasoning_result import EvidenceType, Hypothesis, HypothesisLabel
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    EntityOverlap,
    SemanticAssessment,
)


class TestEvidenceChain:
    def setup_method(self):
        self.chain = DefaultEvidenceChain()

    def test_empty_input_produces_no_evidence(self):
        evidence = self.chain.build([], [], [])
        assert len(evidence) == 0

    def test_evidence_from_hypothesis_derivation(self):
        hyp = Hypothesis(
            id="h1",
            label=HypothesisLabel.DUPLICATE,
            text="duplicate hypothesis",
            confidence=0.8,
            supporting_premises=["high_similarity", "concept_match"],
            contradicting_premises=["entity_mismatch"],
        )
        evidence = self.chain.build([hyp], [], [])
        assert len(evidence) >= 2
        evidence_types = {e.evidence_type for e in evidence}
        assert EvidenceType.SUPPORTING in evidence_types
        assert EvidenceType.CONTRADICTING in evidence_types

    def test_evidence_from_assessment(self):
        hyp = Hypothesis(
            id="h1",
            label=HypothesisLabel.DUPLICATE,
            text="duplicate hypothesis",
            confidence=0.8,
        )
        assessment = SemanticAssessment(
            semantic_similarity=0.85,
            concept_overlap=ConceptOverlap(
                overlap_score=0.75,
                shared_concepts=["python", "programming"],
            ),
            entity_overlap=EntityOverlap(
                overlap_score=0.6,
                shared_entities=["Python"],
            ),
        )
        evidence = self.chain.build([hyp], [], [], assessment)
        assert len(evidence) >= 3
        sim_evidence = [e for e in evidence if "semantic similarity" in e.text.lower()]
        assert sim_evidence

    def test_evidence_deduplication(self):
        hyp = Hypothesis(
            id="h1",
            label=HypothesisLabel.DUPLICATE,
            text="duplicate hypothesis",
            confidence=0.8,
            supporting_premises=["high_similarity"],
        )
        evidence = self.chain.build([hyp], [], [])
        before = len(evidence)
        evidence2 = self.chain.build([hyp], [], [])
        assert len(evidence2) == before

    def test_conflict_evidence_from_assessment(self):
        nondup_hyp = Hypothesis(
            id="h2",
            label=HypothesisLabel.NOT_DUPLICATE,
            text="not duplicate hypothesis",
            confidence=0.7,
        )
        assessment = SemanticAssessment(
            semantic_similarity=0.3,
            entity_overlap=EntityOverlap(
                conflicts=["entity conflict detected"],
            ),
            conflicts=[
                Conflict(conflict_type="entity", description="Different entities", severity=0.8),
            ],
        )
        evidence = self.chain.build([nondup_hyp], [], [], assessment)
        conflict_evidence = [e for e in evidence if "entity conflict" in e.text.lower() or "conflict" in e.text.lower()]
        assert conflict_evidence
