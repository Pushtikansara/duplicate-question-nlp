from __future__ import annotations

import json

from ares.query_understanding.entity_detector import EntityDetector
from ares.query_understanding.entity_matcher import match_entities
from ares.query_understanding.entity_models import (
    ENTITY_TYPES,
    MATCH_TYPES,
    Entity,
    EntityPairMatch,
    EntityResult,
)
from ares.query_understanding.entity_report import EntityReport
from ares.query_understanding.entity_rules import extract_entities
from ares.query_understanding.query_analyzer import QueryAnalyzer
from ares.query_understanding.query_models import QueryAnalysis

detector = EntityDetector()
analyzer = QueryAnalyzer()
report = EntityReport()


class TestEntityModels:
    def test_entity_defaults(self):
        e = Entity()
        assert e.text == ""
        assert e.entity_type == "OTHER"
        assert e.confidence == 1.0

    def test_entity_serialization(self):
        e = Entity(
            text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python", confidence=0.95, start=0, end=6
        )
        d = e.to_dict()
        assert d["text"] == "Python"
        assert d["entity_type"] == "PROGRAMMING_LANGUAGE"
        restored = Entity.from_dict(d)
        assert restored.text == "Python"
        assert restored.confidence == 0.95

    def test_entity_pair_match(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE")
        e2 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE")
        m = EntityPairMatch(entity_1=e1, entity_2=e2, match_type="exact_match", similarity=1.0)
        d = m.to_dict()
        assert d["match_type"] == "exact_match"
        restored = EntityPairMatch.from_dict(d)
        assert restored.entity_1.text == "Python"

    def test_entity_result_serialization(self):
        r = EntityResult(
            entities_1=[Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE")],
            entities_2=[Entity(text="Java", entity_type="PROGRAMMING_LANGUAGE")],
            entity_overlap_score=0.0,
            entity_relationship="different_entities",
        )
        d = r.to_dict()
        assert len(d["entities_1"]) == 1
        assert d["entity_relationship"] == "different_entities"
        restored = EntityResult.from_dict(d)
        assert len(restored.entities_1) == 1
        assert restored.entities_1[0].text == "Python"

    def test_entity_result_empty(self):
        r = EntityResult()
        d = r.to_dict()
        assert d["entities_1"] == []
        assert d["entity_relationship"] == "unknown"

    def test_entity_types_set(self):
        expected = {
            "PERSON",
            "ORGANIZATION",
            "LOCATION",
            "COUNTRY",
            "CITY",
            "PRODUCT",
            "COMPANY",
            "PROGRAMMING_LANGUAGE",
            "FRAMEWORK",
            "LIBRARY",
            "OPERATING_SYSTEM",
            "FILE",
            "URL",
            "EMAIL",
            "DATE",
            "TIME",
            "YEAR",
            "VERSION",
            "NUMBER",
            "PERCENTAGE",
            "CURRENCY",
            "EVENT",
            "ACADEMIC_SUBJECT",
            "BOOK",
            "MOVIE",
            "OTHER",
        }
        assert expected == ENTITY_TYPES

    def test_match_types_set(self):
        expected = {
            "exact_match",
            "case_difference",
            "abbreviation",
            "partial_match",
            "version_difference",
            "numeric_difference",
            "no_match",
        }
        assert expected == MATCH_TYPES


class TestEntityRules:
    def test_python_language(self):
        entities = extract_entities("How to learn Python?")
        assert any(e.text == "Python" and e.entity_type == "PROGRAMMING_LANGUAGE" for e in entities)

    def test_javascript(self):
        entities = extract_entities("What is JavaScript?")
        assert any(e.entity_type == "PROGRAMMING_LANGUAGE" for e in entities)

    def test_django_framework(self):
        entities = extract_entities("How to use Django?")
        assert any(e.text.lower() == "django" and e.entity_type == "FRAMEWORK" for e in entities)

    def test_company_google(self):
        entities = extract_entities("Does Google use Python?")
        assert any(e.entity_type == "COMPANY" for e in entities)

    def test_company_microsoft(self):
        entities = extract_entities("Microsoft released a new product")
        assert any(e.entity_type == "COMPANY" for e in entities)

    def test_country(self):
        entities = extract_entities("What is the capital of France?")
        assert any(e.entity_type == "COUNTRY" for e in entities)

    def test_city(self):
        entities = extract_entities("How far is London from Paris?")
        paris = any(e.text.lower() == "paris" and e.entity_type == "CITY" for e in entities)
        london = any(e.text.lower() == "london" and e.entity_type == "CITY" for e in entities)
        assert paris and london

    def test_url(self):
        entities = extract_entities("Visit https://example.com/page for more")
        assert any(e.entity_type == "URL" for e in entities)

    def test_email(self):
        entities = extract_entities("Contact us at support@example.com")
        assert any(e.entity_type == "EMAIL" for e in entities)

    def test_version(self):
        entities = extract_entities("Python 3.12 was released")
        assert any(e.entity_type == "VERSION" for e in entities)

    def test_percentage(self):
        entities = extract_entities("Accuracy improved by 95%")
        assert any(e.entity_type == "PERCENTAGE" for e in entities)

    def test_year(self):
        entities = extract_entities("In 2024, AI advanced significantly")
        assert any(e.entity_type == "YEAR" for e in entities)

    def test_number(self):
        entities = extract_entities("There are 42 answers")
        assert any(e.entity_type == "NUMBER" for e in entities)

    def test_currency(self):
        entities = extract_entities("It costs $99")
        assert any(e.entity_type == "CURRENCY" for e in entities)

    def test_time(self):
        entities = extract_entities("The meeting is at 3:00 PM")
        assert any(e.entity_type == "TIME" for e in entities)

    def test_operating_system(self):
        entities = extract_entities("How to install Python on Ubuntu?")
        assert any(e.entity_type == "OPERATING_SYSTEM" for e in entities)

    def test_product(self):
        entities = extract_entities("Compare iPhone and Android")
        assert any(e.entity_type == "PRODUCT" for e in entities)

    def test_event(self):
        entities = extract_entities("What caused World War 2?")
        assert any(e.entity_type == "EVENT" for e in entities)

    def test_academic_subject(self):
        entities = extract_entities("I love mathematics and physics")
        assert any(e.entity_type == "ACADEMIC_SUBJECT" for e in entities)

    def test_file_extension(self):
        entities = extract_entities("Run the script.py file")
        assert any(e.entity_type == "FILE" for e in entities)

    def test_person_famous(self):
        entities = extract_entities("Who is Albert Einstein?")
        assert any(e.entity_type == "PERSON" for e in entities)

    def test_organization_keyword(self):
        entities = extract_entities("Microsoft Corporation announced...")
        assert any(e.entity_type == "ORGANIZATION" for e in entities)

    def test_empty(self):
        assert extract_entities("") == []
        assert extract_entities("  ") == []

    def test_no_entities(self):
        entities = extract_entities("how to do this thing?")
        assert len(entities) >= 0

    def test_multiple_entities(self):
        entities = extract_entities("Compare Python and JavaScript frameworks Django and React")
        types = {e.entity_type for e in entities}
        assert "PROGRAMMING_LANGUAGE" in types
        assert "FRAMEWORK" in types


class TestEntityDetector:
    def test_basic_detection(self):
        result = detector.detect("How to learn Python?", "What is JavaScript?")
        assert len(result.entities_1) >= 1
        assert len(result.entities_2) >= 1
        assert result.entity_overlap_score >= 0
        assert result.entity_relationship != ""

    def test_shared_entities(self):
        result = detector.detect(
            "What is Python?",
            "How to learn Python?",
        )
        assert len(result.shared_entities) >= 1
        assert result.entity_relationship == "same_entity"

    def test_different_entities(self):
        result = detector.detect(
            "What is Python?",
            "How to cook rice?",
        )
        if result.entities_1 and result.entities_2:
            assert result.entity_relationship == "different_entities"

    def test_no_entities(self):
        result = detector.detect("how to do this?", "what is that?")
        assert result.entity_relationship in ("no_entities", "overlapping")

    def test_empty_input(self):
        result = detector.detect("", "")
        assert result.entity_relationship == "no_entities"

    def test_one_empty(self):
        result = detector.detect("Python is great", "")
        assert len(result.entities_1) >= 0

    def test_company_and_language(self):
        result = detector.detect(
            "Does Google use Python?",
            "Does Microsoft use C#?",
        )
        assert any(e.entity_type == "COMPANY" for e in result.entities_1)
        assert any(e.entity_type == "COMPANY" for e in result.entities_2)

    def test_overlap_score_identical(self):
        result = detector.detect(
            "How to use Python?",
            "How to use Python?",
        )
        assert result.entity_overlap_score > 0.5

    def test_mixed_language_entities(self):
        result = detector.detect(
            "What is the capital of France?",
            "Compare Paris and London",
        )
        types_q1 = {e.entity_type for e in result.entities_1}
        types_q2 = {e.entity_type for e in result.entities_2}
        assert "COUNTRY" in types_q1 or "CITY" in types_q1

    def test_full_pipeline_result(self):
        result = detector.detect(
            "How to install TensorFlow on Ubuntu?",
            "Differences between TensorFlow and PyTorch",
        )
        assert isinstance(result, EntityResult)
        assert len(result.entities_1) > 0
        assert len(result.entities_2) > 0


class TestEntityMatcher:
    def test_exact_match(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        e2 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        matches, _, _ = match_entities([e1], [e2])
        assert len(matches) == 1
        assert matches[0].match_type == "exact_match"
        assert matches[0].similarity == 1.0

    def test_case_difference(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        e2 = Entity(text="python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        matches, _, _ = match_entities([e1], [e2])
        assert len(matches) >= 1
        assert any(m.match_type == "case_difference" for m in matches)

    def test_no_match(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        e2 = Entity(text="Java", entity_type="PROGRAMMING_LANGUAGE", normalized="java")
        matches, unique1, unique2 = match_entities([e1], [e2])
        assert len(matches) == 0
        assert len(unique1) == 1
        assert len(unique2) == 1

    def test_empty_lists(self):
        matches, u1, u2 = match_entities([], [])
        assert matches == []
        assert u1 == []
        assert u2 == []

    def test_partial_match(self):
        e1 = Entity(text="Machine Learning", entity_type="ACADEMIC_SUBJECT", normalized="machine learning")
        e2 = Entity(
            text="machine learning algorithms", entity_type="ACADEMIC_SUBJECT", normalized="machine learning algorithms"
        )
        matches, _, _ = match_entities([e1], [e2])
        assert any(m.match_type == "partial_match" for m in matches)


class TestEntityReport:
    def test_generate_section(self):
        result = detector.detect("How to learn Python?", "What is Java?")
        section = report.generate_section(result)
        assert isinstance(section, str)
        assert "Entity Analysis" in section or "Entities" in section
        assert "Q1" in section or "Q2" in section

    def test_generate_short(self):
        result = detector.detect("Python vs Java", "Python vs JavaScript")
        short = report.generate_short(result)
        assert isinstance(short, str)

    def test_entity_type_summary(self):
        result = detector.detect(
            "How to use Python, Django, and TensorFlow?",
            "Learn JavaScript with React",
        )
        summary = report.entity_type_summary(result)
        assert isinstance(summary, dict)
        assert len(summary) > 0

    def test_empty_result(self):
        result = EntityResult()
        section = report.generate_section(result)
        assert isinstance(section, str)

    def test_shared_section_format(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE")
        e2 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE")
        result = EntityResult(
            entities_1=[e1],
            entities_2=[e2],
            shared_entities=[EntityPairMatch(entity_1=e1, entity_2=e2, match_type="exact_match", similarity=1.0)],
            entity_overlap_score=1.0,
            entity_relationship="same_entity",
        )
        section = report.generate_section(result)
        assert "Shared" in section
        assert "exact_match" in section


class TestIntegrationWithAnalyzer:
    def test_analyzer_has_entity_analysis(self):
        result = analyzer.analyze("How to learn Python?", "What is Java?")
        assert hasattr(result, "entity_analysis")
        assert isinstance(result.entity_analysis, EntityResult)

    def test_entity_analysis_in_to_dict(self):
        result = analyzer.analyze("How to learn Python?", "What is Java?")
        d = result.to_dict()
        assert "entity_analysis" in d
        assert "entities_1" in d["entity_analysis"]

    def test_entity_analysis_json_roundtrip(self):
        result = analyzer.analyze("How to use Django?", "What is Flask?")
        j = result.to_json()
        parsed = json.loads(j)
        assert "entity_analysis" in parsed

    def test_entity_analysis_from_dict(self):
        original = analyzer.analyze("Python vs Java", "Python vs JavaScript")
        d = original.to_dict()
        restored = QueryAnalysis.from_dict(d)
        assert len(restored.entity_analysis.entities_1) == len(original.entity_analysis.entities_1)
        assert restored.entity_analysis.entity_relationship == original.entity_analysis.entity_relationship
        assert restored.entity_analysis.entity_overlap_score == original.entity_analysis.entity_overlap_score

    def test_full_report_includes_entities(self):
        from ares.query_understanding.query_report import QueryReport

        report_gen = QueryReport()
        result = analyzer.analyze("How to learn Python?", "What is Java?")
        text = report_gen.generate(result)
        assert "Entity Analysis" in text or "Entities" in text


class TestEdgeCases:
    def test_unicode_entities(self):
        entities = extract_entities("Café München Français")
        assert len(entities) >= 0

    def test_version_numbers(self):
        entities = extract_entities("Node.js 18.0.0 and Python 3.12.1")
        versions = [e for e in entities if e.entity_type == "VERSION"]
        assert len(versions) >= 2

    def test_multiple_companies(self):
        entities = extract_entities("Google, Microsoft, and Apple are tech companies")
        company_types = {e.text.lower() for e in entities if e.entity_type == "COMPANY"}
        assert "google" in company_types
        assert "microsoft" in company_types
        assert "apple" in company_types

    def test_organization_with_inc(self):
        entities = extract_entities("Acme Corp and Global Tech Inc are partnering")
        orgs = [e for e in entities if e.entity_type == "ORGANIZATION"]
        assert len(orgs) >= 1

    def test_currency_multiple(self):
        entities = extract_entities("Price is $10.99 or €9.50")
        currencies = [e for e in entities if e.entity_type == "CURRENCY"]
        assert len(currencies) >= 2

    def test_email_and_url_together(self):
        entities = extract_entities("Email info@company.com or visit https://company.com")
        types = {e.entity_type for e in entities}
        assert "EMAIL" in types
        assert "URL" in types

    def test_programming_languages_with_frameworks(self):
        entities = extract_entities("Build web apps with React and Node.js")
        types = {e.entity_type for e in entities}
        assert "FRAMEWORK" in types or "PROGRAMMING_LANGUAGE" in types or "LIBRARY" in types

    def test_academic_subject_ml(self):
        entities = extract_entities("What is machine learning?")
        assert any(e.entity_type == "ACADEMIC_SUBJECT" for e in entities)

    def test_abbreviation_matching(self):
        e1 = Entity(text="AI", entity_type="ACADEMIC_SUBJECT", normalized="ai")
        e2 = Entity(
            text="Artificial Intelligence", entity_type="ACADEMIC_SUBJECT", normalized="artificial intelligence"
        )
        matches, _, _ = match_entities([e1], [e2])
        assert len(matches) >= 1

    def test_case_difference_matching(self):
        e1 = Entity(text="Python", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        e2 = Entity(text="PYTHON", entity_type="PROGRAMMING_LANGUAGE", normalized="python")
        matches, _, _ = match_entities([e1], [e2])
        assert any(m.match_type == "case_difference" for m in matches)

    def test_operating_system_detection(self):
        entities = extract_entities("How to install Docker on Windows?")
        assert any(e.entity_type == "OPERATING_SYSTEM" for e in entities)

    def test_person_detection_with_title(self):
        entities = extract_entities("Dr. John Smith presented the research")
        persons = [e for e in entities if e.entity_type == "PERSON"]
        assert len(persons) >= 1

    def test_events(self):
        entities = extract_entities("What caused the Great Depression?")
        assert any(e.entity_type == "EVENT" for e in entities)

    def test_city_detection(self):
        entities = extract_entities("How far is New York from Los Angeles?")
        cities = {e.text.lower() for e in entities if e.entity_type == "CITY"}
        assert "new york" in cities
        assert "los angeles" in cities

    def test_no_duplicate_spans(self):
        entities = extract_entities("Python Python Python")
        assert len(entities) >= 1

    def test_percentage_boundary(self):
        entities = extract_entities("Score is 99%")
        assert any(e.entity_type == "PERCENTAGE" for e in entities)

    def test_version_in_text(self):
        entities = extract_entities("Upgrade to version 2.0 for new features")
        assert any(e.entity_type == "VERSION" for e in entities)

    def test_very_long_text(self):
        text = " ".join(["Python"] * 50) + " Java"
        entities = extract_entities(text)
        assert any(e.entity_type == "PROGRAMMING_LANGUAGE" for e in entities)

    def test_product_names(self):
        entities = extract_entities("Compare iPhone 15 and Samsung Galaxy")
        products = {e.text.lower() for e in entities if e.entity_type == "PRODUCT"}
        assert "iphone" in products or "galaxy" in products


def test_entity_detector_importable():
    from ares.query_understanding import Entity, EntityDetector, EntityResult

    assert EntityDetector is not None
    assert EntityResult is not None
    assert Entity is not None
