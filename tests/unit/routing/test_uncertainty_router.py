from __future__ import annotations

from duplicate_question_app._reasoning.reasoning_result import ConfidenceChain, ProcessingMetadata, ReasoningResult
from duplicate_question_app._routing.uncertainty_router import DefaultUncertaintyRouter
from duplicate_question_app._semantic_intelligence.semantic_assessment import Conflict, SemanticAssessment


class TestDefaultUncertaintyRouter:
    def setup_method(self):
        self.router = DefaultUncertaintyRouter()

    def test_high_cross_encoder_confidence_no_escalation(self):
        result = self.router.should_escalate(0.95, None, None)
        assert not result.should_escalate
        assert result.uncertainty_score == 0.0

    def test_low_cross_encoder_confidence_escalation(self):
        result = self.router.should_escalate(0.2, None, None)
        assert result.should_escalate
        assert "CrossEncoder" in result.contributing_factors[0]

    def test_cross_encoder_at_threshold(self):
        result = self.router.should_escalate(0.4, None, None)
        assert not result.should_escalate

    def test_cross_encoder_below_threshold(self):
        result = self.router.should_escalate(0.39, None, None)
        assert result.should_escalate

    def test_low_semantic_confidence_escalation(self):
        assessment = SemanticAssessment(semantic_similarity=0.8, confidence=0.3)
        result = self.router.should_escalate(0.9, assessment, None)
        assert result.should_escalate
        assert any("Semantic" in f for f in result.contributing_factors)

    def test_semantic_at_threshold(self):
        assessment = SemanticAssessment(semantic_similarity=0.8, confidence=0.5)
        result = self.router.should_escalate(0.9, assessment, None)
        assert not result.should_escalate

    def test_assessment_with_conflicts_escalation(self):
        assessment = SemanticAssessment(
            semantic_similarity=0.8,
            confidence=0.8,
            conflicts=[Conflict(conflict_type="test", description="conflict", severity=0.8)],
        )
        result = self.router.should_escalate(0.9, assessment, None)
        assert result.should_escalate
        assert any("conflict" in f.lower() for f in result.contributing_factors)

    def test_assessment_with_minor_conflicts_no_escalation(self):
        assessment = SemanticAssessment(
            semantic_similarity=0.8,
            confidence=0.8,
            conflicts=[Conflict(conflict_type="test", description="minor", severity=0.0)],
        )
        result = self.router.should_escalate(0.9, assessment, None)
        assert result.should_escalate

    def test_high_reasoning_uncertainty_escalation(self):
        reasoning = ReasoningResult(
            decision="uncertain",
            confidence=0.3,
            uncertainty=0.8,
            confidence_chain=ConfidenceChain(decision_confidence=0.3),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.9, None, reasoning)
        assert result.should_escalate
        assert any("uncertainty" in f.lower() for f in result.contributing_factors)

    def test_reasoning_at_threshold(self):
        reasoning = ReasoningResult(
            decision="duplicate",
            confidence=0.6,
            uncertainty=0.6,
            confidence_chain=ConfidenceChain(decision_confidence=0.6),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.9, None, reasoning)
        assert not result.should_escalate

    def test_low_reasoning_confidence_escalation(self):
        reasoning = ReasoningResult(
            decision="uncertain",
            confidence=0.3,
            uncertainty=0.3,
            confidence_chain=ConfidenceChain(decision_confidence=0.3),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.9, None, reasoning)
        assert result.should_escalate
        assert any("confidence" in f.lower() for f in result.contributing_factors)

    def test_all_high_confidence_no_escalation(self):
        assessment = SemanticAssessment(semantic_similarity=0.9, confidence=0.9)
        reasoning = ReasoningResult(
            decision="duplicate",
            confidence=0.9,
            uncertainty=0.1,
            confidence_chain=ConfidenceChain(decision_confidence=0.9),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.95, assessment, reasoning)
        assert not result.should_escalate
        assert result.uncertainty_score == 0.0

    def test_multiple_contributing_factors(self):
        assessment = SemanticAssessment(
            semantic_similarity=0.2,
            confidence=0.3,
            conflicts=[Conflict(conflict_type="test", description="mismatch", severity=0.9)],
        )
        reasoning = ReasoningResult(
            decision="uncertain",
            confidence=0.2,
            uncertainty=0.9,
            confidence_chain=ConfidenceChain(decision_confidence=0.2),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.1, assessment, reasoning)
        assert result.should_escalate
        assert len(result.contributing_factors) >= 3

    def test_low_semantic_similarity_escalation(self):
        assessment = SemanticAssessment(semantic_similarity=0.2, confidence=0.8)
        result = self.router.should_escalate(0.9, assessment, None)
        assert result.should_escalate

    def test_uncertainty_score_max_value(self):
        reasoning = ReasoningResult(
            decision="uncertain",
            confidence=0.1,
            uncertainty=0.95,
            confidence_chain=ConfidenceChain(decision_confidence=0.1),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.router.should_escalate(0.05, None, reasoning)
        assert result.uncertainty_score >= 0.8

    def test_none_inputs(self):
        result = self.router.should_escalate(None, None, None)
        assert not result.should_escalate
        assert result.uncertainty_score == 0.0

    def test_reasoning_result_empty_defaults_escalate(self):
        reasoning = ReasoningResult()
        result = self.router.should_escalate(0.9, None, reasoning)
        assert result.should_escalate
        assert "uncertainty" in result.contributing_factors[0].lower()
