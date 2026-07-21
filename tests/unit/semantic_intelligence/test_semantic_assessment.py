"""Tests for SemanticAssessment dataclasses."""

from duplicate_question_app._semantic_intelligence.semantic_assessment import (
    ConceptOverlap,
    Conflict,
    ContextSimilarity,
    EntityOverlap,
    EvidenceItem,
    IntentSimilarity,
    ProcessingMetadata,
    Recommendation,
    RelationSimilarity,
    SemanticAssessment,
)


class TestConceptOverlap:
    def test_defaults(self):
        co = ConceptOverlap()
        assert co.overlap_score == 0.0
        assert co.shared_concepts == []

    def test_with_data(self):
        co = ConceptOverlap(overlap_score=0.75, shared_concepts=["A", "B"], missing_in_a=["C"], total_a=3, total_b=2)
        assert co.overlap_score == 0.75
        assert len(co.shared_concepts) == 2


class TestEntityOverlap:
    def test_defaults(self):
        eo = EntityOverlap()
        assert eo.overlap_score == 0.0
        assert eo.conflicts == []

    def test_with_conflicts(self):
        eo = EntityOverlap(conflicts=["Type mismatch"], overlap_score=0.5)
        assert len(eo.conflicts) == 1


class TestIntentSimilarity:
    def test_defaults(self):
        ins = IntentSimilarity()
        assert ins.score == 0.0
        assert ins.reason == ""

    def test_with_data(self):
        ins = IntentSimilarity(score=0.9, confidence=0.85, reason="Exact match")
        assert ins.score == 0.9


class TestRelationSimilarity:
    def test_defaults(self):
        rs = RelationSimilarity()
        assert rs.score == 0.0


class TestContextSimilarity:
    def test_defaults(self):
        cs = ContextSimilarity()
        assert cs.domain_match is False


class TestConflict:
    def test_create_conflict(self):
        c = Conflict(conflict_type="domain_mismatch", description="Domains differ", severity=0.8)
        assert c.conflict_type == "domain_mismatch"
        assert c.severity == 0.8


class TestEvidenceItem:
    def test_create_evidence(self):
        e = EvidenceItem(category="intent", status="match", message="Intent matches", confidence=0.9)
        assert e.category == "intent"
        assert e.status == "match"


class TestRecommendation:
    def test_enum_values(self):
        assert Recommendation.DUPLICATE.value == "DUPLICATE"
        assert Recommendation.NOT_DUPLICATE.value == "NOT_DUPLICATE"
        assert Recommendation.UNCERTAIN.value == "UNCERTAIN"


class TestProcessingMetadata:
    def test_defaults(self):
        pm = ProcessingMetadata()
        assert pm.processing_time_ms == 0.0
        assert pm.stages == {}
        assert pm.components_used == []


class TestSemanticAssessment:
    def test_empty_assessment(self):
        sa = SemanticAssessment()
        assert sa.semantic_similarity == 0.0
        assert sa.recommendation == Recommendation.UNCERTAIN
        assert sa.conflicts == []
        assert sa.supporting_evidence == []

    def test_full_assessment(self):
        sa = SemanticAssessment(
            semantic_similarity=0.85,
            confidence=0.8,
            recommendation=Recommendation.DUPLICATE,
            recommendation_reason="High similarity",
        )
        assert sa.semantic_similarity == 0.85
        assert sa.recommendation == Recommendation.DUPLICATE

    def test_to_dict(self):
        sa = SemanticAssessment(
            semantic_similarity=0.75,
            confidence=0.7,
            recommendation=Recommendation.DUPLICATE,
            recommendation_reason="Test",
        )
        d = sa.to_dict()
        assert d["semantic_similarity"] == 0.75
        assert d["recommendation"] == "DUPLICATE"
        assert d["recommendation_reason"] == "Test"
        assert "concept_overlap" in d
        assert "entity_overlap" in d
        assert "intent_similarity" in d
        assert "relation_similarity" in d
        assert "context_similarity" in d
        assert "conflicts" in d
        assert "supporting_evidence" in d
        assert "confidence_detail" in d
        assert "processing_metadata" in d

    def test_to_dict_with_conflicts(self):
        sa = SemanticAssessment(
            conflicts=[Conflict(conflict_type="test", description="test conflict", severity=0.5)],
            supporting_evidence=[EvidenceItem(category="test", status="info", message="test evidence")],
        )
        d = sa.to_dict()
        assert len(d["conflicts"]) == 1
        assert d["conflicts"][0]["type"] == "test"
        assert len(d["supporting_evidence"]) == 1
        assert d["supporting_evidence"][0]["category"] == "test"
