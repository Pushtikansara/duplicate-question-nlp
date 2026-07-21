from __future__ import annotations

from duplicate_question_app._reasoning.hypothesis_generator import DefaultHypothesisGenerator
from duplicate_question_app._reasoning.reasoning_result import HypothesisLabel, Premise
from duplicate_question_app._semantic_intelligence.semantic_assessment import ConceptOverlap, SemanticAssessment


class TestHypothesisGenerator:
    def setup_method(self):
        self.generator = DefaultHypothesisGenerator()

    def _make_premises(self, count=3, category="concept", prefix="A"):
        return [
            Premise(id=f"{prefix}_{i}", text=f"premise {prefix}_{i}", source="test", category=category, confidence=0.9)
            for i in range(count)
        ]

    def test_empty_premises_generates_hypotheses(self):
        hypotheses = self.generator.generate([], [])
        assert len(hypotheses) >= 2
        labels = {h.label for h in hypotheses}
        assert HypothesisLabel.DUPLICATE in labels
        assert HypothesisLabel.NOT_DUPLICATE in labels

    def test_high_similarity_generates_duplicate_hypothesis(self):
        premises_a = self._make_premises(3, prefix="A")
        premises_b = self._make_premises(3, prefix="B")
        assessment = SemanticAssessment(
            semantic_similarity=0.85,
            concept_overlap=ConceptOverlap(overlap_score=0.6),
        )
        hypotheses = self.generator.generate(premises_a, premises_b, assessment)
        dup_hyp = [h for h in hypotheses if h.label == HypothesisLabel.DUPLICATE]
        nondup_hyp = [h for h in hypotheses if h.label == HypothesisLabel.NOT_DUPLICATE]
        assert dup_hyp
        assert nondup_hyp
        assert dup_hyp[0].confidence > nondup_hyp[0].confidence

    def test_low_similarity_generates_not_duplicate_hypothesis(self):
        premises_a = self._make_premises(3, prefix="A")
        premises_b = self._make_premises(3, prefix="B")
        assessment = SemanticAssessment(
            semantic_similarity=0.15,
            concept_overlap=ConceptOverlap(overlap_score=0.1),
        )
        hypotheses = self.generator.generate(premises_a, premises_b, assessment)
        dup_hyp = [h for h in hypotheses if h.label == HypothesisLabel.DUPLICATE]
        nondup_hyp = [h for h in hypotheses if h.label == HypothesisLabel.NOT_DUPLICATE]
        assert dup_hyp
        assert nondup_hyp
        assert nondup_hyp[0].confidence > dup_hyp[0].confidence

    def test_uncertain_hypothesis_when_scores_close(self):
        premises_a = self._make_premises(2, prefix="A")
        premises_b = self._make_premises(2, prefix="B")
        assessment = SemanticAssessment(
            semantic_similarity=0.8,
            concept_overlap=ConceptOverlap(overlap_score=0.1),
        )
        hypotheses = self.generator.generate(premises_a, premises_b, assessment)
        uncertain = [h for h in hypotheses if h.label == HypothesisLabel.UNCERTAIN]
        assert uncertain

    def test_hypothesis_has_derivation(self):
        premises_a = self._make_premises(2, prefix="A")
        premises_b = self._make_premises(2, prefix="B")
        assessment = SemanticAssessment(
            semantic_similarity=0.8,
            concept_overlap=ConceptOverlap(overlap_score=0.7),
        )
        hypotheses = self.generator.generate(premises_a, premises_b, assessment)
        for h in hypotheses:
            assert h.derivation
            assert "semantic_similarity" in h.derivation
