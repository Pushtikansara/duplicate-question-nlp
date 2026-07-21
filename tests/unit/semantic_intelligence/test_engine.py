"""Integration tests for SemanticIntelligenceEngine."""

import pytest

from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRelation, SemanticRepresentation
from duplicate_question_app._semantic_intelligence.engine import SemanticIntelligenceEngine
from duplicate_question_app._semantic_intelligence.semantic_assessment import Recommendation


@pytest.fixture
def engine():
    return SemanticIntelligenceEngine()


@pytest.fixture
def rep_install_python():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
        entities=[{"name": "Python", "type": "language"}],
        actions=["install"],
        objects=["python"],
        relationships=[SemanticRelation(source_id="INSTALL", target_id="PYTHON", relation_type="acts_on")],
        domain="technology",
        intent_summary="install python",
        semantic_confidence=0.85,
    )


@pytest.fixture
def rep_setup_python():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="SETUP", label="setup", normalized_form="SETUP"),
            SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
        ],
        entities=[{"name": "Python", "type": "language"}],
        actions=["setup"],
        objects=["python"],
        relationships=[SemanticRelation(source_id="SETUP", target_id="PYTHON", relation_type="acts_on")],
        domain="technology",
        intent_summary="setup python",
        semantic_confidence=0.80,
    )


@pytest.fixture
def rep_delete_java():
    return SemanticRepresentation(
        concepts=[
            SemanticConcept(id="DELETE", label="delete", normalized_form="DELETE"),
            SemanticConcept(id="JAVA", label="Java", normalized_form="JAVA"),
        ],
        entities=[{"name": "Java", "type": "language"}],
        actions=["delete"],
        objects=["java"],
        relationships=[SemanticRelation(source_id="DELETE", target_id="JAVA", relation_type="acts_on")],
        domain="programming",
        intent_summary="delete java",
        semantic_confidence=0.90,
    )


class TestSemanticIntelligenceEngine:
    def test_assess_identical(self, engine, rep_install_python):
        assessment = engine.assess(rep_install_python, rep_install_python)
        assert assessment.semantic_similarity > 0.5
        assert assessment.concept_overlap.overlap_score == 1.0
        assert assessment.entity_overlap.overlap_score == 1.0
        assert assessment.intent_similarity.score > 0.5
        assert assessment.confidence > 0.5

    def test_assess_partial_match(self, engine, rep_install_python, rep_setup_python):
        assessment = engine.assess(rep_install_python, rep_setup_python)
        assert 0.0 < assessment.semantic_similarity < 1.0
        assert "PYTHON" in assessment.concept_overlap.shared_concepts

    def test_assess_no_match(self, engine, rep_install_python, rep_delete_java):
        assessment = engine.assess(rep_install_python, rep_delete_java)
        assert assessment.semantic_similarity < 0.5
        assert len(assessment.concept_overlap.shared_concepts) == 0

    def test_assess_output_contains_all_fields(self, engine, rep_install_python, rep_setup_python):
        assessment = engine.assess(rep_install_python, rep_setup_python)
        assert assessment.semantic_similarity >= 0.0
        assert assessment.concept_overlap is not None
        assert assessment.entity_overlap is not None
        assert assessment.intent_similarity is not None
        assert assessment.relation_similarity is not None
        assert assessment.context_similarity is not None
        assert assessment.conflicts is not None
        assert assessment.supporting_evidence is not None
        assert assessment.confidence >= 0.0
        assert assessment.confidence_detail != {}
        assert assessment.recommendation in (
            Recommendation.DUPLICATE,
            Recommendation.NOT_DUPLICATE,
            Recommendation.UNCERTAIN,
        )
        assert assessment.recommendation_reason != ""
        assert assessment.processing_metadata is not None
        assert assessment.processing_metadata.components_used is not None

    def test_assess_similar_questions_yield_duplicate(self, engine):
        rep_a = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="HOW", label="how", normalized_form="HOW"),
                SemanticConcept(id="INSTALL", label="install", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
            ],
            entities=[{"name": "Python", "type": "language"}],
            actions=["install"],
            objects=["python"],
            intent_summary="how to install python",
            domain="technology",
            semantic_confidence=0.9,
        )
        rep_b = SemanticRepresentation(
            concepts=[
                SemanticConcept(id="HOW", label="how", normalized_form="HOW"),
                SemanticConcept(id="INSTALL", label="installing", normalized_form="INSTALL"),
                SemanticConcept(id="PYTHON", label="Python", normalized_form="PYTHON"),
            ],
            entities=[{"name": "Python", "type": "language"}],
            actions=["install"],
            objects=["python"],
            intent_summary="how to install python version 3",
            domain="technology",
            semantic_confidence=0.9,
        )
        assessment = engine.assess(rep_a, rep_b)
        assert assessment.recommendation in (Recommendation.DUPLICATE, Recommendation.UNCERTAIN)

    def test_assess_different_yield_not_duplicate(self, engine, rep_install_python, rep_delete_java):
        assessment = engine.assess(rep_install_python, rep_delete_java)
        assert assessment.recommendation == Recommendation.NOT_DUPLICATE

    def test_assess_processing_metadata(self, engine, rep_install_python, rep_setup_python):
        assessment = engine.assess(rep_install_python, rep_setup_python)
        assert assessment.processing_metadata.processing_time_ms > 0
        assert "concept_matching" in assessment.processing_metadata.stages
        assert "entity_matching" in assessment.processing_metadata.stages
        assert len(assessment.processing_metadata.components_used) == 10

    def test_to_dict_serialization(self, engine, rep_install_python, rep_setup_python):
        assessment = engine.assess(rep_install_python, rep_setup_python)
        d = assessment.to_dict()
        assert "semantic_similarity" in d
        assert "concept_overlap" in d
        assert "entity_overlap" in d
        assert "intent_similarity" in d
        assert "relation_similarity" in d
        assert "context_similarity" in d
        assert "conflicts" in d
        assert "supporting_evidence" in d
        assert "confidence" in d
        assert "confidence_detail" in d
        assert "recommendation" in d
        assert "recommendation_reason" in d
        assert "processing_metadata" in d
