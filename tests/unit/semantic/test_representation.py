"""Tests for SemanticRepresentation dataclasses."""

from duplicate_question_app._semantic.representation import (
    AmbiguityEntry,
    ProcessingMetadata,
    SemanticConcept,
    SemanticRelation,
    SemanticRepresentation,
    SemanticRoleAssignment,
)


class TestSemanticConcept:
    def test_create_concept(self):
        c = SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL")
        assert c.id == "INSTALL"
        assert c.label == "install"
        assert c.normalized_form == "INSTALL"
        assert c.confidence == 1.0
        assert c.source == "keyword"

    def test_concept_with_metadata(self):
        c = SemanticConcept(
            id="PYTHON", label="Python", normalized_form="PYTHON", confidence=0.9, metadata={"pos": "NOUN"}
        )
        assert c.metadata["pos"] == "NOUN"


class TestSemanticRelation:
    def test_create_relation(self):
        r = SemanticRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on", confidence=0.85)
        assert r.source_id == "INSTALL"
        assert r.target_id == "PYTHON"
        assert r.relation_type == "acts_on"


class TestSemanticRoleAssignment:
    def test_create_role(self):
        ra = SemanticRoleAssignment(role="ACTION", concept_ids=["INSTALL", "DEBUG"], confidence=0.9)
        assert ra.role == "ACTION"
        assert ra.concept_ids == ["INSTALL", "DEBUG"]


class TestAmbiguityEntry:
    def test_create_ambiguity(self):
        a = AmbiguityEntry(type="low_confidence", description="Low confidence", confidence=0.3)
        assert a.type == "low_confidence"


class TestProcessingMetadata:
    def test_create_metadata(self):
        m = ProcessingMetadata(total_concepts=5, total_relations=3, processing_time_ms=12.5)
        assert m.total_concepts == 5
        assert m.total_relations == 3


class TestSemanticRepresentation:
    def test_empty_representation(self):
        sr = SemanticRepresentation()
        assert sr.concepts == []
        assert sr.relationships == []
        assert sr.semantic_confidence == 0.0
        assert sr.processing_metadata.total_concepts == 0

    def test_representation_with_data(self):
        concepts = [
            SemanticConcept(id="A", label="a", normalized_form="A"),
            SemanticConcept(id="B", label="b", normalized_form="B"),
        ]
        relations = [SemanticRelation(source_id="A", target_id="B", relation_type="related_to")]
        sr = SemanticRepresentation(
            concepts=concepts, relationships=relations, domain="technology", intent_summary="install"
        )

        assert len(sr.concepts) == 2
        assert len(sr.relationships) == 1
        assert sr.domain == "technology"
        assert sr.intent_summary == "install"

    def test_to_dict(self):
        sr = SemanticRepresentation(domain="test", intent_summary="query")
        d = sr.to_dict()
        assert d["domain"] == "test"
        assert d["intent_summary"] == "query"
        assert d["semantic_confidence"] == 0.0

    def test_to_dict_with_concepts(self):
        concepts = [SemanticConcept(id="X", label="x", normalized_form="X", confidence=0.9)]
        sr = SemanticRepresentation(concepts=concepts)
        d = sr.to_dict()
        assert d["concepts"][0]["id"] == "X"
        assert d["concepts"][0]["confidence"] == 0.9
