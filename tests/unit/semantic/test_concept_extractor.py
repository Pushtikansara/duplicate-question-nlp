"""Tests for DefaultConceptExtractor."""

import pytest

from duplicate_question_app._linguistic_intelligence.profile import AnalysisConfidence, Keyword, LinguisticProfile
from duplicate_question_app._semantic.concept_extractor import DefaultConceptExtractor


@pytest.fixture
def extractor():
    return DefaultConceptExtractor()


@pytest.fixture
def profile_with_args():
    return LinguisticProfile(
        keywords=[],
        entities=[],
        intent="install",
        intent_confidence=0.9,
        domain="technology",
        domain_confidence=0.8,
        question_type="how",
        language="en",
        language_confidence=0.95,
        analysis_confidence=AnalysisConfidence(overall=0.9),
    )


class TestDefaultConceptExtractor:
    def test_extract_intent_concept(self, extractor, profile_with_args):
        concepts = extractor.extract(profile_with_args)
        ids = [c.id for c in concepts]
        assert "INSTALL" in ids

    def test_extract_domain_concept(self, extractor, profile_with_args):
        concepts = extractor.extract(profile_with_args)
        ids = [c.id for c in concepts]
        assert "TECHNOLOGY" in ids

    def test_extract_keywords(self):
        profile = LinguisticProfile(
            keywords=[
                Keyword(word="python", score=0.9, is_entity=False),
                Keyword(word="ubuntu", score=0.8, is_entity=False),
            ],
            entities=[],
            analysis_confidence=AnalysisConfidence(),
        )
        extractor = DefaultConceptExtractor()
        concepts = extractor.extract(profile)
        ids = [c.id for c in concepts]
        assert "PYTHON" in ids
        assert "UBUNTU" in ids

    def test_extract_entities(self):
        profile = LinguisticProfile(
            keywords=[Keyword(word="Windows", score=0.95, is_entity=True)],
            entities=[{"value": "Windows", "type": "OS", "confidence": 0.95}],
            entity_count=1,
            analysis_confidence=AnalysisConfidence(),
        )
        extractor = DefaultConceptExtractor()
        concepts = extractor.extract(profile)
        ids = [c.id for c in concepts]
        assert "WINDOWS" in ids

    def test_no_duplicate_ids(self, extractor, profile_with_args):
        concepts = extractor.extract(profile_with_args)
        ids = [c.id for c in concepts]
        assert len(ids) == len(set(ids))

    def test_empty_profile(self):
        profile = LinguisticProfile(analysis_confidence=AnalysisConfidence())
        extractor = DefaultConceptExtractor()
        concepts = extractor.extract(profile)
        assert concepts == []
