from __future__ import annotations

from duplicate_question_app._reasoning.reasoning_engine import ReasoningEngine
from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import ConceptOverlap, SemanticAssessment


class TestReasoningEngine:
    def setup_method(self):
        self.engine = ReasoningEngine()

    def _make_simple_rep(self, label_prefix: str) -> SemanticRepresentation:
        return SemanticRepresentation(
            concepts=[
                SemanticConcept(
                    id=f"{label_prefix}_c1",
                    label=f"{label_prefix} concept 1",
                    normalized_form=f"{label_prefix.lower()}_concept_1",
                    confidence=0.9,
                ),
                SemanticConcept(
                    id=f"{label_prefix}_c2",
                    label=f"{label_prefix} concept 2",
                    normalized_form=f"{label_prefix.lower()}_concept_2",
                    confidence=0.8,
                ),
            ],
            entities=[],
            actions=[],
            objects=[],
            attributes=[],
            relationships=[],
            intent_summary=f"asking about {label_prefix.lower()}",
            domain="programming",
        )

    def test_reason_returns_result_with_all_fields(self):
        rep_a = self._make_simple_rep("Python")
        rep_b = self._make_simple_rep("Python")
        result = self.engine.reason(rep_a, rep_b)
        assert result is not None
        assert len(result.premises) > 0
        assert len(result.hypotheses) > 0
        assert result.decision in ("duplicate", "not_duplicate", "uncertain")
        assert 0 <= result.confidence <= 1
        assert 0 <= result.uncertainty <= 1
        assert result.decision_reason
        assert result.reasoning_trace is not None
        assert result.reasoning_graph is not None

    def test_reason_with_assessment(self):
        rep_a = self._make_simple_rep("Python")
        rep_b = self._make_simple_rep("Java")
        assessment = SemanticAssessment(
            semantic_similarity=0.3,
            concept_overlap=ConceptOverlap(overlap_score=0.2),
        )
        result = self.engine.reason(rep_a, rep_b, assessment=assessment)
        assert result is not None
        assert len(result.supporting_evidence) > 0 or len(result.contradicting_evidence) > 0

    def test_reason_with_cross_encoder_score(self):
        rep_a = self._make_simple_rep("Python")
        rep_b = self._make_simple_rep("Python")
        result = self.engine.reason(rep_a, rep_b, cross_encoder_score=0.9)
        assert result.decision is not None

    def test_reasoning_trace_has_steps(self):
        rep_a = self._make_simple_rep("A")
        rep_b = self._make_simple_rep("B")
        result = self.engine.reason(rep_a, rep_b)
        assert len(result.reasoning_trace.steps) > 0
        steps = result.reasoning_trace.to_dict()
        assert len(steps) > 0
        assert steps[0]["component"]
        assert steps[0]["action"]

    def test_confidence_chain_is_populated(self):
        rep_a = self._make_simple_rep("A")
        rep_b = self._make_simple_rep("B")
        result = self.engine.reason(rep_a, rep_b)
        chain = result.confidence_chain
        assert chain.premise_confidence > 0
        assert len(chain.sources) > 0

    def test_processing_metadata(self):
        rep_a = self._make_simple_rep("A")
        rep_b = self._make_simple_rep("B")
        result = self.engine.reason(rep_a, rep_b)
        meta = result.processing_metadata
        assert meta.total_premises > 0
        assert meta.total_hypotheses >= 2
        assert meta.processing_time_ms > 0
        assert len(meta.components_used) > 0

    def test_similar_reps_produce_duplicate_decision(self):
        rep_a = SemanticRepresentation(
            concepts=[SemanticConcept(id="c1", label="python", normalized_form="python", confidence=0.9)],
            actions=["learn"],
            objects=["programming"],
            intent_summary="asking how to learn programming",
        )
        rep_b = SemanticRepresentation(
            concepts=[SemanticConcept(id="c2", label="python", normalized_form="python", confidence=0.9)],
            actions=["study"],
            objects=["coding"],
            intent_summary="asking how to study coding",
        )
        assessment = SemanticAssessment(semantic_similarity=0.8, concept_overlap=ConceptOverlap(overlap_score=0.7))
        result = self.engine.reason(rep_a, rep_b, assessment=assessment, cross_encoder_score=0.85)
        assert result.decision == "duplicate"

    def test_different_reps_produce_not_duplicate_or_uncertain(self):
        rep_a = SemanticRepresentation(
            concepts=[SemanticConcept(id="c1", label="python", normalized_form="python", confidence=0.9)],
            intent_summary="asking about python programming",
        )
        rep_b = SemanticRepresentation(
            concepts=[SemanticConcept(id="c2", label="cooking", normalized_form="cooking", confidence=0.9)],
            intent_summary="asking about recipes",
        )
        assessment = SemanticAssessment(semantic_similarity=0.1, concept_overlap=ConceptOverlap(overlap_score=0.0))
        result = self.engine.reason(rep_a, rep_b, assessment=assessment)
        assert result.decision in ("not_duplicate", "uncertain")

    def test_reasoning_result_to_dict(self):
        rep_a = self._make_simple_rep("A")
        rep_b = self._make_simple_rep("B")
        result = self.engine.reason(rep_a, rep_b)
        d = result.to_dict()
        assert "premises" in d
        assert "hypotheses" in d
        assert "supporting_evidence" in d
        assert "contradicting_evidence" in d
        assert "reasoning_graph" in d
        assert "reasoning_trace" in d
        assert "confidence_chain" in d
        assert "decision" in d
        assert "confidence" in d
        assert "uncertainty" in d
        assert "processing_metadata" in d

    def test_reasoning_trace_recording(self):
        from duplicate_question_app._reasoning.reasoning_trace import TraceRecorder

        tracer = TraceRecorder()
        with tracer.step("test_component", "test_action"):
            pass
        assert len(tracer.trace.steps) == 1
        assert tracer.trace.steps[0].component == "test_component"
        assert tracer.trace.steps[0].action == "test_action"

    def test_reasoning_result_missing_assessment(self):
        rep_a = self._make_simple_rep("A")
        rep_b = self._make_simple_rep("B")
        result = self.engine.reason(rep_a, rep_b)
        assert len(result.hypotheses) >= 2
