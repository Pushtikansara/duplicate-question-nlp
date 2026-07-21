from __future__ import annotations

from duplicate_question_app._agents.agent import (
    ConfidenceAgent,
    ConflictAgent,
    ConsensusAgent,
    EntityAgent,
    EvidenceAgent,
    IntentAgent,
    RelationAgent,
    SemanticAgent,
)
from duplicate_question_app._reasoning.reasoning_result import (
    ConfidenceChain,
    Evidence,
    EvidenceType,
    Hypothesis,
    HypothesisLabel,
    Premise,
    ProcessingMetadata,
    ReasoningGraph,
    ReasoningResult,
    ReasoningTrace,
)
from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    EntityOverlap,
    IntentSimilarity,
    RelationSimilarity,
    SemanticAssessment,
)


def _make_simple_rep(label_prefix: str = "python") -> SemanticRepresentation:
    return SemanticRepresentation(
        concepts=[SemanticConcept(id="c1", label=label_prefix, normalized_form=label_prefix, confidence=0.9)],
        entities=[],
        actions=[],
        objects=[],
        attributes=[],
        relationships=[],
        intent_summary=f"asking about {label_prefix.lower()}",
        domain="programming",
    )


def _make_reasoning_result(
    decision: str = "duplicate",
    confidence: float = 0.8,
    uncertainty: float = 0.2,
    hyp_confidences: list[float] | None = None,
) -> ReasoningResult:
    if hyp_confidences is None:
        hyp_confidences = [0.8, 0.2]
    return ReasoningResult(
        premises=[Premise(id="p1", text="test", source="a", category="intent", confidence=0.9)],
        hypotheses=[
            Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=hyp_confidences[0]),
            Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=hyp_confidences[1]),
        ],
        supporting_evidence=[
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.8,
                weight=1.0,
            ),
        ],
        contradicting_evidence=[
            Evidence(
                id="e2",
                hypothesis_id="h2",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.6,
                weight=0.5,
            ),
        ],
        confidence_chain=ConfidenceChain(
            premise_confidence=0.9,
            hypothesis_confidence=hyp_confidences[0],
            evidence_confidence=0.8,
            reasoning_confidence=0.8,
            decision_confidence=confidence,
        ),
        decision=decision,
        confidence=confidence,
        uncertainty=uncertainty,
        reasoning_graph=ReasoningGraph(),
        reasoning_trace=ReasoningTrace(),
        processing_metadata=ProcessingMetadata(),
    )


class TestIntentAgent:
    def setup_method(self):
        self.agent = IntentAgent()

    def test_name(self):
        assert self.agent.name == "intent_agent"

    def test_no_intent_data(self):
        rep = _make_simple_rep()
        rep.intent_summary = None
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"
        assert result.confidence == 0.5

    def test_matching_intents_with_assessment(self):
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("python")
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            intent_similarity=IntentSimilarity(score=0.85, confidence=0.9, reason="match"),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "duplicate"
        assert result.confidence >= 0.7
        assert len(result.supporting_evidence) > 0

    def test_diverging_intents_with_assessment(self):
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("cooking")
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            intent_similarity=IntentSimilarity(score=0.15, confidence=0.8, reason="different"),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "not_duplicate"
        assert result.confidence <= 0.4

    def test_exact_text_match(self):
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("python")
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "duplicate"

    def test_different_text_no_assessment(self):
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("cooking")
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "uncertain"

    def test_missing_one_intent(self):
        rep_a = _make_simple_rep("python")
        rep_b = _make_simple_rep("cooking")
        rep_b.intent_summary = None
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "uncertain"
        assert len(result.warnings) > 0

    def test_processing_time(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.processing_time_ms >= 0


class TestSemanticAgent:
    def setup_method(self):
        self.agent = SemanticAgent()

    def test_name(self):
        assert self.agent.name == "semantic_agent"

    def test_high_similarity(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(semantic_similarity=0.85, concept_overlap=ConceptOverlap(overlap_score=0.8))
        rr = _make_reasoning_result(decision="duplicate", confidence=0.8)
        result = self.agent.evaluate(rep, rep, assessment, rr)
        assert result.recommendation == "duplicate"
        assert result.confidence >= 0.5

    def test_low_similarity(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(semantic_similarity=0.15, concept_overlap=ConceptOverlap(overlap_score=0.1))
        rr = _make_reasoning_result(decision="not_duplicate", confidence=0.2)
        result = self.agent.evaluate(rep, rep, assessment, rr)
        assert result.recommendation == "not_duplicate"

    def test_mid_similarity_uncertain(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(semantic_similarity=0.5, concept_overlap=ConceptOverlap(overlap_score=0.4))
        result = self.agent.evaluate(rep, rep, assessment, None)
        assert result.recommendation == "uncertain"

    def test_no_assessment(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"
        assert len(result.warnings) > 0

    def test_disagreement_with_reasoning(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(semantic_similarity=0.85, concept_overlap=ConceptOverlap(overlap_score=0.8))
        rr = _make_reasoning_result(decision="not_duplicate", confidence=0.2)
        result = self.agent.evaluate(rep, rep, assessment, rr)
        assert len(result.contradicting_evidence) > 0

    def test_concept_count_mismatch(self):
        rep_a = _make_simple_rep()
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="c1", label="python", normalized_form="python", confidence=0.9),
                SemanticConcept(id="c2", label="java", normalized_form="java", confidence=0.8),
            ],
            entities=[],
            actions=[],
            objects=[],
            attributes=[],
            relationships=[],
            intent_summary="asking about python",
        )
        assessment = SemanticAssessment(semantic_similarity=0.7, concept_overlap=ConceptOverlap(overlap_score=0.5))
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.confidence >= 0


class TestEntityAgent:
    def setup_method(self):
        self.agent = EntityAgent()

    def test_name(self):
        assert self.agent.name == "entity_agent"

    def test_no_entities(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"

    def test_shared_entities(self):
        rep_a = SemanticRepresentation(entities=[{"label": "python"}, {"label": "java"}])
        rep_b = SemanticRepresentation(entities=[{"label": "python"}, {"label": "java"}])
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "duplicate"
        assert result.confidence > 0.5

    def test_conflicting_entities(self):
        rep_a = SemanticRepresentation(entities=[{"label": "python"}, {"label": "java"}])
        rep_b = SemanticRepresentation(entities=[{"label": "cooking"}, {"label": "baking"}])
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "not_duplicate"

    def test_partial_overlap(self):
        rep_a = SemanticRepresentation(entities=[{"label": "python"}, {"label": "java"}, {"label": "sql"}])
        rep_b = SemanticRepresentation(entities=[{"label": "python"}, {"label": "java"}, {"label": "cooking"}])
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert result.recommendation == "duplicate"

    def test_with_assessment_entity_overlap(self):
        rep_a = SemanticRepresentation(entities=[{"label": "python"}])
        rep_b = SemanticRepresentation(entities=[{"label": "python"}])
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            entity_overlap=EntityOverlap(overlap_score=1.0, shared_entities=["python"], conflicts=[]),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "duplicate"

    def test_entity_conflicts_from_assessment(self):
        rep_a = SemanticRepresentation(entities=[{"label": "python"}])
        rep_b = SemanticRepresentation(entities=[{"label": "java"}])
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            entity_overlap=EntityOverlap(overlap_score=0.0, shared_entities=[], conflicts=["type conflict"]),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert len(result.contradicting_evidence) > 0


class TestRelationAgent:
    def setup_method(self):
        self.agent = RelationAgent()

    def test_name(self):
        assert self.agent.name == "relation_agent"

    def test_no_relations(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"
        # Should still produce NEUTRAL evidence
        assert len(result.supporting_evidence) == 0
        assert len(result.contradicting_evidence) == 0

    def test_high_relation_similarity(self):
        rep_a = SemanticRepresentation(relationships=[{"relation_type": "is_a"}])
        rep_b = SemanticRepresentation(relationships=[{"relation_type": "is_a"}])
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            relation_similarity=RelationSimilarity(
                score=0.85, matching_relations=[{}], missing_in_a=[], missing_in_b=[], total_a=1, total_b=1
            ),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "duplicate"

    def test_low_relation_similarity(self):
        rep_a = SemanticRepresentation(relationships=[{"relation_type": "is_a"}])
        rep_b = SemanticRepresentation(relationships=[{"relation_type": "has_property"}])
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            relation_similarity=RelationSimilarity(
                score=0.15, matching_relations=[], missing_in_a=[{}], missing_in_b=[{}], total_a=1, total_b=1
            ),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "not_duplicate"

    def test_asymmetric_relations(self):
        rep_a = SemanticRepresentation(relationships=[{"relation_type": "is_a"}])
        rep_b = SemanticRepresentation(relationships=[])
        result = self.agent.evaluate(rep_a, rep_b, None, None)
        assert len(result.warnings) > 0

    def test_shared_relation_types(self):
        rep_a = SemanticRepresentation(relationships=[{"relation_type": "is_a"}, {"relation_type": "has_property"}])
        rep_b = SemanticRepresentation(relationships=[{"relation_type": "is_a"}, {"relation_type": "part_of"}])
        assessment = SemanticAssessment(
            semantic_similarity=0.0,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            relation_similarity=RelationSimilarity(
                score=0.5, matching_relations=[{}], missing_in_a=[{}], missing_in_b=[{}], total_a=2, total_b=2
            ),
        )
        result = self.agent.evaluate(rep_a, rep_b, assessment, None)
        assert result.recommendation == "uncertain"


class TestConflictAgent:
    def setup_method(self):
        self.agent = ConflictAgent()

    def test_name(self):
        assert self.agent.name == "conflict_agent"

    def test_no_conflicts(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(semantic_similarity=0.8, concept_overlap=ConceptOverlap(overlap_score=0.7))
        rr = ReasoningResult(
            premises=[Premise(id="p1", text="test", source="a", category="intent", confidence=0.9)],
            hypotheses=[
                Hypothesis(id="h1", label=HypothesisLabel.DUPLICATE, text="dup", confidence=0.8),
                Hypothesis(id="h2", label=HypothesisLabel.NOT_DUPLICATE, text="non", confidence=0.2),
            ],
            supporting_evidence=[
                Evidence(
                    id="e1",
                    hypothesis_id="h1",
                    evidence_type=EvidenceType.SUPPORTING,
                    text="support",
                    confidence=0.8,
                    weight=1.0,
                )
            ],
            contradicting_evidence=[],
            confidence_chain=ConfidenceChain(
                premise_confidence=0.9,
                hypothesis_confidence=0.8,
                evidence_confidence=0.8,
                reasoning_confidence=0.8,
                decision_confidence=0.8,
            ),
            decision="duplicate",
            confidence=0.8,
            uncertainty=0.1,
            reasoning_graph=ReasoningGraph(),
            reasoning_trace=ReasoningTrace(),
            processing_metadata=ProcessingMetadata(),
        )
        result = self.agent.evaluate(rep, rep, assessment, rr)
        assert result.recommendation == "duplicate"
        assert result.confidence >= 0.7

    def test_assessment_conflicts(self):
        rep = _make_simple_rep()
        assessment = SemanticAssessment(
            semantic_similarity=0.1,
            concept_overlap=ConceptOverlap(overlap_score=0.0),
            conflicts=[Conflict(conflict_type="domain_mismatch", description="Different domains", severity=0.8)],
        )
        result = self.agent.evaluate(rep, rep, assessment, None)
        assert len(result.contradicting_evidence) >= 1

    def test_high_uncertainty(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="uncertain", confidence=0.3, uncertainty=0.85)
        result = self.agent.evaluate(rep, rep, None, rr)
        assert len(result.warnings) > 0

    def test_low_confidence_premises(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="uncertain", confidence=0.3)
        rr.premises = [Premise(id="p1", text="low confidence premise", source="a", category="concept", confidence=0.3)]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.confidence >= 0

    def test_both_hypotheses_supported(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="uncertain", confidence=0.5, hyp_confidences=[0.5, 0.5])
        rr.hypotheses[0].supporting_premises = ["premise1"]
        rr.hypotheses[1].supporting_premises = ["premise2"]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert len(result.warnings) >= 1


class TestConfidenceAgent:
    def setup_method(self):
        self.agent = ConfidenceAgent()

    def test_name(self):
        assert self.agent.name == "confidence_agent"

    def test_no_reasoning_result(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"

    def test_high_confidence(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.85)
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.recommendation == "duplicate"

    def test_low_confidence(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="not_duplicate", confidence=0.15)
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.recommendation == "not_duplicate"

    def test_overconfidence_detected(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.8)
        rr.confidence_chain = ConfidenceChain(
            premise_confidence=0.9,
            hypothesis_confidence=0.85,
            evidence_confidence=0.2,
            reasoning_confidence=0.8,
            decision_confidence=0.8,
        )
        result = self.agent.evaluate(rep, rep, None, rr)
        assert len(result.warnings) >= 1
        assert "overconfidence" in str(result.warnings).lower()

    def test_underconfidence_detected(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.4)
        rr.confidence_chain = ConfidenceChain(
            premise_confidence=0.9,
            hypothesis_confidence=0.2,
            evidence_confidence=0.8,
            reasoning_confidence=0.4,
            decision_confidence=0.4,
        )
        result = self.agent.evaluate(rep, rep, None, rr)
        assert len(result.warnings) >= 1
        assert "underconfidence" in str(result.warnings).lower()

    def test_chain_detail_in_evidence(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.8)
        result = self.agent.evaluate(rep, rep, None, rr)
        supporting_texts = [e.text for e in result.supporting_evidence]
        assert any("premise" in t.lower() for t in supporting_texts)


class TestEvidenceAgent:
    def setup_method(self):
        self.agent = EvidenceAgent()

    def test_name(self):
        assert self.agent.name == "evidence_agent"

    def test_no_reasoning_result(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"

    def test_supporting_dominates(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.8)
        rr.supporting_evidence = [
            Evidence(
                id=f"e{i}",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text=f"support {i}",
                confidence=0.8,
                weight=1.0,
            )
            for i in range(5)
        ]
        rr.contradicting_evidence = [
            Evidence(
                id="cx",
                hypothesis_id="h2",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.5,
                weight=0.5,
            )
        ]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.recommendation == "duplicate"

    def test_contradicting_dominates(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="not_duplicate", confidence=0.2)
        rr.supporting_evidence = [
            Evidence(
                id="ex",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.8,
                weight=1.0,
            )
        ]
        rr.contradicting_evidence = [
            Evidence(
                id=f"e{i}",
                hypothesis_id="h2",
                evidence_type=EvidenceType.CONTRADICTING,
                text=f"contra {i}",
                confidence=0.7,
                weight=1.0,
            )
            for i in range(5)
        ]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.recommendation == "not_duplicate"

    def test_balanced_evidence(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="uncertain", confidence=0.5)
        rr.supporting_evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="support",
                confidence=0.8,
                weight=1.0,
            )
        ]
        rr.contradicting_evidence = [
            Evidence(
                id="e2",
                hypothesis_id="h2",
                evidence_type=EvidenceType.CONTRADICTING,
                text="contra",
                confidence=0.8,
                weight=1.0,
            )
        ]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert result.recommendation == "uncertain"

    def test_duplicate_detection(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.8)
        rr.supporting_evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="same text",
                confidence=0.8,
                weight=1.0,
            ),
            Evidence(
                id="e2",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="same text",
                confidence=0.8,
                weight=1.0,
            ),
        ]
        result = self.agent.evaluate(rep, rep, None, rr)
        assert len(result.warnings) >= 1

    def test_low_quality_warning(self):
        rep = _make_simple_rep()
        rr = _make_reasoning_result(decision="duplicate", confidence=0.3)
        rr.supporting_evidence = [
            Evidence(
                id="e1",
                hypothesis_id="h1",
                evidence_type=EvidenceType.SUPPORTING,
                text="low",
                confidence=0.2,
                weight=0.2,
            ),
        ]
        result = self.agent.evaluate(rep, rep, None, rr)
        quality_warnings = [w for w in result.warnings if "quality" in w.lower()]
        assert len(quality_warnings) >= 1


class TestConsensusAgent:
    def setup_method(self):
        self.agent = ConsensusAgent()

    def test_name(self):
        assert self.agent.name == "consensus_agent"

    def test_always_uncertain(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert result.recommendation == "uncertain"
        assert result.confidence == 1.0

    def test_no_supporting_or_contradicting(self):
        rep = _make_simple_rep()
        result = self.agent.evaluate(rep, rep, None, None)
        assert len(result.supporting_evidence) == 0
        assert len(result.contradicting_evidence) == 0
