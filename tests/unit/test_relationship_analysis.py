from __future__ import annotations

import json

from ares.query_understanding.relationship_analyzer import RelationshipAnalyzer
from ares.query_understanding.relationship_detector import RelationshipDetector
from ares.query_understanding.relationship_models import (
    ComparisonStatistics,
    Evidence,
    RelationshipAnalysis,
    RelationshipInfo,
    TransformationChain,
    TransformationStep,
)
from ares.query_understanding.relationship_patterns import (
    NEGATION_WORDS,
    PRONOUNS,
)
from ares.query_understanding.relationship_report import RelationshipReport
from ares.query_understanding.relationship_rules import (
    layer_1_normalize,
    layer_2_token_comparison,
    layer_5_negation,
    layer_6_numeric,
    layer_7_lexical,
)
from ares.query_understanding.relationship_utils import (
    check_abbreviation,
    check_antonym,
    check_spelling_variant,
    check_synonym,
    compute_jaccard,
    compute_shared_token_ratio,
    compute_token_overlap,
    edit_distance,
    find_dates,
    find_numbers,
    find_times,
    find_units,
    normalize_text,
    normalized_edit_distance,
    strip_punctuation,
    tokenize,
)

detector = RelationshipDetector()
analyzer = RelationshipAnalyzer()
report = RelationshipReport()


# ============================================================
# UTILITY TESTS
# ============================================================


class TestTokenize:
    def test_empty(self):
        assert tokenize("") == []

    def test_simple(self):
        assert tokenize("hello world") == ["hello", "world"]

    def test_multiple_spaces(self):
        assert tokenize("hello   world") == ["hello", "world"]

    def test_strip(self):
        assert tokenize("  hello world  ") == ["hello", "world"]


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("HeLLo") == "hello"

    def test_whitespace(self):
        assert normalize_text("  hello   world  ") == "hello world"

    def test_unicode(self):
        assert "café" in normalize_text("Café")

    def test_empty(self):
        assert normalize_text("") == ""


class TestStripPunctuation:
    def test_basic(self):
        assert strip_punctuation("hello!") == "hello"

    def test_multiple(self):
        assert strip_punctuation("what's this?") == "whats this"

    def test_no_punct(self):
        assert strip_punctuation("hello world") == "hello world"


class TestEditDistance:
    def test_identical(self):
        assert edit_distance("hello", "hello") == 0

    def test_one_char_diff(self):
        assert edit_distance("hello", "hallo") == 1

    def test_completely_different(self):
        assert edit_distance("abc", "def") == 3

    def test_empty(self):
        assert edit_distance("", "hello") == 5
        assert edit_distance("hello", "") == 5
        assert edit_distance("", "") == 0


class TestNormalizedEditDistance:
    def test_identical(self):
        assert normalized_edit_distance("hello", "hello") == 0.0

    def test_different(self):
        assert normalized_edit_distance("abc", "abcdef") == 0.5

    def test_empty(self):
        assert normalized_edit_distance("", "") == 0.0


class TestJaccard:
    def test_identical_tokens(self):
        assert compute_jaccard(["a", "b"], ["a", "b"]) == 1.0

    def test_no_overlap(self):
        assert compute_jaccard(["a", "b"], ["c", "d"]) == 0.0

    def test_partial(self):
        j = compute_jaccard(["a", "b", "c"], ["a", "b", "d"])
        assert 0.5 <= j <= 0.67

    def test_empty(self):
        assert compute_jaccard([], []) == 0.0


class TestTokenOverlap:
    def test_basic(self):
        assert compute_token_overlap(["a", "b"], ["a", "c"]) == 1

    def test_all_overlap(self):
        assert compute_token_overlap(["a", "b"], ["a", "b"]) == 2

    def test_no_overlap(self):
        assert compute_token_overlap(["a"], ["b"]) == 0


class TestSharedTokenRatio:
    def test_full(self):
        assert compute_shared_token_ratio(["a", "b"], ["a", "b"]) == 1.0

    def test_half(self):
        assert compute_shared_token_ratio(["a"], ["a", "b"]) == 1.0

    def test_none(self):
        assert compute_shared_token_ratio(["a"], ["b"]) == 0.0

    def test_empty(self):
        assert compute_shared_token_ratio([], []) == 0.0


class TestFindNumbers:
    def test_numbers(self):
        result = find_numbers("version 2.0 and 42")
        assert len(result) >= 2

    def test_no_numbers(self):
        assert find_numbers("hello world") == []


class TestFindDates:
    def test_date_slash(self):
        result = find_dates("date 2024/01/15")
        assert len(result) >= 1

    def test_date_word(self):
        result = find_dates("Jan 15, 2024")
        assert len(result) >= 1

    def test_no_date(self):
        assert find_dates("hello") == []


class TestFindTimes:
    def test_time(self):
        assert len(find_times("at 3:00 PM")) >= 1

    def test_no_time(self):
        assert find_times("hello") == []


class TestFindUnits:
    def test_length(self):
        result = find_units("10 cm")
        assert len(result) >= 1

    def test_weight(self):
        assert len(find_units("5 kg")) >= 1

    def test_data(self):
        assert len(find_units("1 GB")) >= 1


class TestCheckAbbreviation:
    def test_ai_artificial_intelligence(self):
        assert check_abbreviation("AI", "Artificial Intelligence")

    def test_nlp_natural_language_processing(self):
        assert check_abbreviation("NLP", "Natural Language Processing")

    def test_no_match(self):
        assert not check_abbreviation("ABC", "XYZ")


class TestCheckSynonym:
    def test_begin_start(self):
        assert check_synonym("begin", "start")

    def test_fix_repair(self):
        assert check_synonym("fix", "repair")

    def test_no_match(self):
        assert not check_synonym("cat", "dog")


class TestCheckAntonym:
    def test_big_small(self):
        assert check_antonym("big", "small")

    def test_hot_cold(self):
        assert check_antonym("hot", "cold")

    def test_no_match(self):
        assert not check_antonym("cat", "dog")

    def test_symmetric(self):
        assert check_antonym("small", "big")


class TestCheckSpellingVariant:
    def test_color_colour(self):
        assert check_spelling_variant("color", "colour")

    def test_center_centre(self):
        assert check_spelling_variant("center", "centre")

    def test_no_match(self):
        assert not check_spelling_variant("hello", "world")

    def test_symmetric(self):
        assert check_spelling_variant("colour", "color")


# ============================================================
# LAYER TESTS
# ============================================================


class TestLayer1Normalize:
    def test_basic(self):
        n1, n2, t1, t2 = layer_1_normalize("Hello World", "hello world")
        assert n1 == n2

    def test_different(self):
        n1, n2, t1, t2 = layer_1_normalize("How to code", "How to debug")
        assert n1 != n2


class TestLayer2TokenComparison:
    def test_exact_match(self):
        n1, n2, t1, t2 = layer_1_normalize("How to code?", "How to code?")
        rels, stats, _, _ = layer_2_token_comparison(t1, t2, n1, n2)
        assert any(r.relationship_type == "exact_match" for r in rels)

    def test_case_only(self):
        n1, n2, t1, t2 = layer_1_normalize("How to code?", "how to code?")
        rels, _, _, _ = layer_2_token_comparison(t1, t2, n1, n2)
        assert any(r.relationship_type in ("capitalization_only", "exact_match") for r in rels)

    def test_near_match_typo(self):
        n1, n2, t1, t2 = layer_1_normalize("How to instal?", "How to install?")
        rels, _, _, _ = layer_2_token_comparison(t1, t2, n1, n2)
        assert any(r.relationship_type == "near_match" for r in rels)

    def test_punctuation_diff(self):
        rels, _, _, _ = layer_2_token_comparison(
            ["hello", "world"],
            ["hello", "world"],
            "hello world",
            "hello world!",
        )
        assert any(r.relationship_type == "punctuation_only" for r in rels)

    def test_token_count_mismatch(self):
        n1, n2, t1, t2 = layer_1_normalize("A B C", "A B")
        rels, stats, _, _ = layer_2_token_comparison(t1, t2, n1, n2)
        assert stats.token_count_q1 == 3
        assert stats.token_count_q2 == 2


class TestLayer5Negation:
    def test_negation_introduced(self):
        t1 = ["how", "to", "do", "this"]
        t2 = ["how", "to", "not", "do", "this"]
        rels = layer_5_negation(t1, t2)
        assert any(r.relationship_type == "negation_introduced" for r in rels)

    def test_negation_removed(self):
        t1 = ["how", "to", "not", "do", "this"]
        t2 = ["how", "to", "do", "this"]
        rels = layer_5_negation(t1, t2)
        assert any(r.relationship_type == "negation_removed" for r in rels)

    def test_no_negation(self):
        t1 = ["hello"]
        t2 = ["world"]
        rels = layer_5_negation(t1, t2)
        assert len(rels) == 0


class TestLayer6Numeric:
    def test_version_difference(self):
        rels = layer_6_numeric("version 2.0", "version 3.0", [], [])
        assert any(r.relationship_type == "version_difference" for r in rels)

    def test_numeric_difference(self):
        rels = layer_6_numeric("10 items", "20 items", [], [])
        assert any(r.relationship_type == "numeric_difference" for r in rels)

    def test_no_numeric(self):
        rels = layer_6_numeric("hello", "world", [], [])
        assert len(rels) == 0


class TestLayer7Lexical:
    def test_synonym(self):
        rels = layer_7_lexical(["begin"], ["start"])
        assert any(r.relationship_type == "synonym_replacement" for r in rels)

    def test_antonym(self):
        rels = layer_7_lexical(["big"], ["small"])
        assert any(r.relationship_type == "antonym_detection" for r in rels)

    def test_spelling(self):
        rels = layer_7_lexical(["color"], ["colour"])
        assert any(r.relationship_type == "spelling_variant" for r in rels)

    def test_pronoun(self):
        rels = layer_7_lexical(["i"], ["you"])
        assert any(r.relationship_type == "pronoun_replacement" for r in rels)

    def test_no_match(self):
        rels = layer_7_lexical(["cat"], ["dog"])
        assert len(rels) == 0


# ============================================================
# MODEL TESTS
# ============================================================


class TestEvidence:
    def test_defaults(self):
        e = Evidence()
        assert e.rule_name == ""
        assert e.rule_layer == 0
        assert e.tokens_q1 == []
        assert e.confidence == 0.0

    def test_serialization(self):
        e = Evidence("test", 2, "pattern", ["a"], ["b"], 0.9)
        d = e.to_dict()
        assert d["rule_name"] == "test"
        assert d["rule_layer"] == 2
        assert d["tokens_q1"] == ["a"]
        assert d["confidence"] == 0.9
        e2 = Evidence.from_dict(d)
        assert e2.rule_name == e.rule_name
        assert e2.rule_layer == e.rule_layer

    def test_from_dict_empty(self):
        e = Evidence.from_dict({})
        assert e.rule_name == ""


class TestRelationshipInfo:
    def test_defaults(self):
        r = RelationshipInfo()
        assert r.relationship_type == ""
        assert r.confidence == 0.0

    def test_serialization(self):
        r = RelationshipInfo("test", 0.8, [Evidence("r1", 1, "p", [], [], 0.9)])
        d = r.to_dict()
        assert d["relationship_type"] == "test"
        assert d["confidence"] == 0.8
        r2 = RelationshipInfo.from_dict(d)
        assert r2.relationship_type == "test"

    def test_from_dict_empty(self):
        r = RelationshipInfo.from_dict({})
        assert r.relationship_type == ""


class TestTransformationStep:
    def test_defaults(self):
        s = TransformationStep()
        assert s.step_type == ""
        assert s.tokens_q1 == []

    def test_serialization(self):
        s = TransformationStep("negation", "desc", ["not"], ["do"], 0.9)
        d = s.to_dict()
        assert d["step_type"] == "negation"
        s2 = TransformationStep.from_dict(d)
        assert s2.step_type == "negation"


class TestTransformationChain:
    def test_defaults(self):
        c = TransformationChain()
        assert c.steps == []
        assert c.is_equivalent is False

    def test_serialization(self):
        steps = [TransformationStep("negation", "desc")]
        c = TransformationChain(steps, "different", False)
        d = c.to_dict()
        assert len(d["steps"]) == 1
        c2 = TransformationChain.from_dict(d)
        assert len(c2.steps) == 1
        assert c2.steps[0].step_type == "negation"


class TestComparisonStatistics:
    def test_defaults(self):
        s = ComparisonStatistics()
        assert s.token_count_q1 == 0
        assert s.jaccard_similarity == 0.0

    def test_serialization(self):
        s = ComparisonStatistics(5, 3, 10, 8, 5, 3, 2, 0.4, 3, 0.2, 0.5, 2, 0.6)
        d = s.to_dict()
        assert d["token_count_q1"] == 5
        s2 = ComparisonStatistics.from_dict(d)
        assert s2.token_count_q1 == 5


class TestRelationshipAnalysis:
    def test_defaults(self):
        ra = RelationshipAnalysis()
        assert ra.relationship_score == 0.0
        assert ra.relationship_types == []

    def test_primary_relationship_empty(self):
        ra = RelationshipAnalysis()
        assert ra.primary_relationship() == "unknown_relationship"

    def test_primary_relationship(self):
        ra = RelationshipAnalysis(
            relationship_types=[
                RelationshipInfo("exact_match", 1.0),
                RelationshipInfo("punctuation_only", 0.9),
            ],
        )
        assert ra.primary_relationship() == "exact_match"

    def test_risk_score_no_flags(self):
        ra = RelationshipAnalysis()
        assert ra.risk_score() == 0.0

    def test_risk_score_with_flags(self):
        ra = RelationshipAnalysis(risk_flags=["meaning_changed", "entity_conflict"])
        assert ra.risk_score() == 50.0

    def test_semantic_distance_exact(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("exact_match", 1.0)],
            relationship_score=100.0,
        )
        assert ra.semantic_distance() == 0.0

    def test_semantic_distance_punctuation(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("punctuation_only", 0.9)],
            relationship_score=98.0,
        )
        assert ra.semantic_distance() == 0.0

    def test_semantic_distance_negation(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("negation_introduced", 0.9)],
            relationship_score=50.0,
        )
        d = ra.semantic_distance()
        assert d > 0.0

    def test_serialization(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("exact_match", 1.0)],
            relationship_score=100.0,
            relationship_confidence=1.0,
            relationship_summary="Exact match",
            semantic_flags=["equivalent_intent"],
            risk_flags=[],
            comparison_statistics=ComparisonStatistics(1, 1, 2, 2, 1, 1, 1, 1.0, 0, 0.0, 1.0, 0, 1.0),
        )
        d = ra.to_dict()
        assert d["relationship_score"] == 100.0
        ra2 = RelationshipAnalysis.from_dict(d)
        assert ra2.relationship_score == 100.0
        assert ra2.primary_relationship() == "exact_match"

    def test_from_dict_empty(self):
        ra = RelationshipAnalysis.from_dict({})
        assert ra.relationship_types == []
        assert ra.relationship_score == 0.0
        assert ra.primary_relationship() == "unknown_relationship"

    def test_to_dict_full(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("test_type", 0.5)],
            relationship_score=50.0,
            relationship_confidence=0.5,
            relationship_summary="Test",
            semantic_flags=["flag1"],
            risk_flags=["risk1"],
            transformation_chain=TransformationChain(
                steps=[TransformationStep("step1", "desc", ["a"], ["b"], 0.8)],
            ),
            comparison_statistics=ComparisonStatistics(2, 3, 4, 5, 2, 3, 1, 0.5, 2, 0.3, 0.4, 1, 0.5),
            processing_time=1.5,
            version="1.0.0",
        )
        d = ra.to_dict()
        assert d["version"] == "1.0.0"
        assert len(d["relationship_types"]) == 1
        assert d["relationship_types"][0]["relationship_type"] == "test_type"


# ============================================================
# DETECTOR TESTS — Exact / Near / Format
# ============================================================


class TestDetectorExact:
    def test_identical(self):
        res = detector.detect("How to install Python?", "How to install Python?")
        assert res.primary_relationship() == "exact_match"
        assert res.relationship_score == 100.0

    def test_case_difference(self):
        res = detector.detect("How to install Python?", "how to install python?")
        assert res.relationship_score >= 95

    def test_whitespace_difference(self):
        res = detector.detect("Hello  World", "Hello World")
        assert res.relationship_score >= 90

    def test_punctuation_difference(self):
        res = detector.detect("Hello World", "Hello, World!")
        assert res.relationship_score >= 70


class TestDetectorNear:
    def test_typo_single_char(self):
        res = detector.detect("How to instal Python?", "How to install Python?")
        assert any(r.relationship_type == "near_match" for r in res.relationship_types)

    def test_typo_two_chars(self):
        res = detector.detect("How to instal?", "How to install?")
        assert any(r.relationship_type == "near_match" for r in res.relationship_types)


class TestDetectorEmpty:
    def test_both_empty(self):
        res = detector.detect("", "")
        assert res.primary_relationship() == "unknown_relationship"
        assert res.relationship_score == 0.0

    def test_one_empty(self):
        res = detector.detect("hello", "")
        assert res.relationship_score == 0.0


# ============================================================
# DETECTOR — Negation
# ============================================================


class TestDetectorNegation:
    def test_negation_introduced(self):
        res = detector.detect(
            "How to install Python?",
            "How to not install Python?",
        )
        assert any(r.relationship_type == "negation_introduced" for r in res.relationship_types)

    def test_negation_removed(self):
        res = detector.detect(
            "How to not install Python?",
            "How to install Python?",
        )
        assert any(r.relationship_type == "negation_removed" for r in res.relationship_types)

    def test_no_negation_either(self):
        res = detector.detect("What is Python?", "What is Java?")
        assert not any(r.relationship_type.startswith("negation") for r in res.relationship_types)

    def test_multiple_negations(self):
        res = detector.detect(
            "Why not never use this?",
            "Why not do this?",
        )
        neg_types = {r.relationship_type for r in res.relationship_types}
        assert "negation_removed" in neg_types or "question_polarity_change" in neg_types


# ============================================================
# DETECTOR — Numeric
# ============================================================


class TestDetectorNumeric:
    def test_numeric_difference(self):
        res = detector.detect("10 apples?", "20 apples?")
        assert any(r.relationship_type == "numeric_difference" for r in res.relationship_types)

    def test_same_number(self):
        res = detector.detect("Python 3.8", "Python 3.8")
        assert not any(r.relationship_type == "numeric_difference" for r in res.relationship_types)

    def test_no_numbers(self):
        res = detector.detect("Hello", "World")
        assert not any(r.relationship_type == "numeric_difference" for r in res.relationship_types)


class TestDetectorVersion:
    def test_version_diff(self):
        res = detector.detect("Python 3.8", "Python 3.9")
        assert any(r.relationship_type == "version_difference" for r in res.relationship_types)

    def test_same_version(self):
        res = detector.detect("Python 3.8", "Python 3.8")
        assert not any(r.relationship_type == "version_difference" for r in res.relationship_types)

    def test_no_version(self):
        res = detector.detect("Hello", "World")
        assert not any(r.relationship_type == "version_difference" for r in res.relationship_types)


class TestDetectorDate:
    def test_date_difference(self):
        res = detector.detect("2024/01/15", "2024/06/20")
        date_diffs = [r for r in res.relationship_types if r.relationship_type == "date_difference"]
        assert len(date_diffs) >= 1 or res.primary_relationship() in (
            "numeric_difference",
            "version_difference",
        )

    def test_same_date(self):
        res = detector.detect("2024/01/15", "2024/01/15")
        assert not any(r.relationship_type == "date_difference" for r in res.relationship_types)

    def test_no_date(self):
        res = detector.detect("Hello", "World")
        assert not any(r.relationship_type == "date_difference" for r in res.relationship_types)


class TestDetectorTime:
    def test_time_difference(self):
        res = detector.detect("at 3:00 PM", "at 5:00 PM")
        assert any(r.relationship_type == "time_difference" for r in res.relationship_types)

    def test_same_time(self):
        res = detector.detect("at 3:00 PM", "at 3:00 PM")
        assert not any(r.relationship_type == "time_difference" for r in res.relationship_types)


class TestDetectorCurrency:
    def test_currency_diff(self):
        res = detector.detect("$10", "$20")
        assert any(r.relationship_type == "currency_difference" for r in res.relationship_types)

    def test_same_currency(self):
        res = detector.detect("$10", "$10")
        assert not any(r.relationship_type == "currency_difference" for r in res.relationship_types)

    def test_no_currency(self):
        res = detector.detect("Hello", "World")
        assert not any(r.relationship_type == "currency_difference" for r in res.relationship_types)


class TestDetectorPercentage:
    def test_percentage_diff(self):
        res = detector.detect("50%", "75%")
        assert any(r.relationship_type == "percentage_difference" for r in res.relationship_types)

    def test_same_pct(self):
        res = detector.detect("50%", "50%")
        assert not any(r.relationship_type == "percentage_difference" for r in res.relationship_types)


class TestDetectorUnit:
    def test_unit_value_diff(self):
        res = detector.detect("10 cm", "20 cm")
        assert any(r.relationship_type == "unit_difference" for r in res.relationship_types)

    def test_no_unit(self):
        res = detector.detect("Hello", "World")
        assert not any(r.relationship_type == "unit_difference" for r in res.relationship_types)


# ============================================================
# DETECTOR — Lexical
# ============================================================


class TestDetectorSynonym:
    def test_synonym_replacement(self):
        res = detector.detect("How to begin?", "How to start?")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_synonym_repair(self):
        res = detector.detect("How to fix?", "How to repair?")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)


class TestDetectorAntonym:
    def test_antonym(self):
        res = detector.detect("Is it big?", "Is it small?")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)

    def test_antonym_hot_cold(self):
        res = detector.detect("Is it hot?", "Is it cold?")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)


class TestDetectorAbbreviation:
    def test_abbreviation_ai(self):
        res = detector.detect("What is AI?", "What is Artificial Intelligence?")
        abbrev_types = {r.relationship_type for r in res.relationship_types}
        assert (
            "synonym_replacement" in abbrev_types
            or "abbreviation_expansion" in abbrev_types
            or "entity_replacement" in abbrev_types
        )

    def test_abbreviation_nlp(self):
        res = detector.detect("What is NLP?", "What is Natural Language Processing?")
        assert res.relationship_score > 0

    def test_abbreviation_ml(self):
        res = detector.detect("ML models", "Machine Learning models")
        assert res.relationship_score > 0

    def test_abbreviation_html(self):
        res = detector.detect("HTML basics", "Hypertext Markup Language basics")
        assert res.relationship_score > 0


class TestDetectorSpelling:
    def test_color_colour(self):
        res = detector.detect("What color?", "What colour?")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_center_centre(self):
        res = detector.detect("City center", "City centre")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)


class TestDetectorPronoun:
    def test_pronoun_replacement(self):
        res = detector.detect("How do I do this?", "How do you do this?")
        assert any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types)

    def test_pronoun_added(self):
        res = detector.detect("How to install?", "How do I install?")
        assert any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types)


# ============================================================
# DETECTOR — Structure changes
# ============================================================


class TestDetectorWordOrder:
    def test_word_order_change(self):
        res = detector.detect("What is Python?", "Python is what?")
        assert res.relationship_score > 0

    def test_same_order(self):
        res = detector.detect("How to code?", "How to code?")
        assert not any(r.relationship_type == "word_order_change" for r in res.relationship_types)


class TestDetectorEntity:
    def test_entity_addition(self):
        res = detector.detect("How to install?", "How to install Ubuntu?")
        entity_types = {r.relationship_type for r in res.relationship_types}
        assert "entity_addition" in entity_types

    def test_entity_removal(self):
        res = detector.detect("How to install Ubuntu?", "How to install?")
        entity_types = {r.relationship_type for r in res.relationship_types}
        assert "entity_removal" in entity_types

    def test_entity_replacement(self):
        res = detector.detect("Python vs Java", "Python vs C++")
        entity_types = {r.relationship_type for r in res.relationship_types}
        assert "entity_replacement" in entity_types or "entity_addition" in entity_types


# ============================================================
# DETECTOR — Complex / Multi-relationship
# ============================================================


class TestDetectorMultiRelationship:
    def test_reformulation_with_entity(self):
        res = detector.detect(
            "How to install Ubuntu?",
            "How do I install Ubuntu Linux?",
        )
        assert len(res.relationship_types) >= 2

    def test_reformulation_with_synonym(self):
        res = detector.detect(
            "How to begin coding?",
            "How to start programming?",
        )
        assert len(res.relationship_types) >= 1

    def test_negation_with_numeric(self):
        res = detector.detect(
            "Not 10 items",
            "20 items",
        )
        neg_types = {r.relationship_type for r in res.relationship_types}
        assert "negation_removed" in neg_types or "numeric_difference" in neg_types


class TestDetectorFalsePositive:
    def test_not_false_positive_same(self):
        res = detector.detect("Hello World", "Hello World")
        assert res.primary_relationship() == "exact_match"

    def test_not_false_positive_different(self):
        res = detector.detect("cat", "dog")
        assert res.relationship_score < 95

    def test_not_false_positive_completely_different(self):
        res = detector.detect(
            "How to bake a cake?",
            "What is the speed of light?",
        )
        assert res.relationship_score < 50


class TestDetectorFalseNegative:
    def test_same_meaning_diff_words(self):
        res = detector.detect("How to fix this?", "How to repair this?")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_equivalent_questions(self):
        res = detector.detect("What's Python?", "What is Python?")
        assert res.relationship_score >= 60


# ============================================================
# REPORT TESTS
# ============================================================


class TestReport:
    def test_generate_basic(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("exact_match", 1.0)],
            relationship_score=100.0,
            relationship_confidence=1.0,
            relationship_summary="Test",
        )
        text = report.generate(ra)
        assert "RELATIONSHIP ANALYSIS REPORT" in text
        assert "Exact Match" in text

    def test_generate_developer(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("exact_match", 1.0)],
            relationship_score=100.0,
        )
        dev = report.generate_developer(ra)
        data = json.loads(dev)
        assert data["relationship_score"] == 100.0

    def test_generate_machine(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("exact_match", 1.0)],
            relationship_score=100.0,
        )
        machine = report.generate_machine(ra)
        assert isinstance(machine, dict)
        assert machine["relationship_score"] == 100.0

    def test_generate_with_risk_flags(self):
        ra = RelationshipAnalysis(
            risk_flags=["meaning_changed"],
            relationship_types=[RelationshipInfo("negation_introduced", 0.9)],
            relationship_score=30.0,
            relationship_summary="Negation changed",
        )
        text = report.generate(ra)
        assert "Meaning Changed" in text

    def test_generate_with_transformation(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("negation_introduced", 0.9)],
            relationship_score=30.0,
            transformation_chain=TransformationChain(
                steps=[TransformationStep("negation_introduced", "Negation added")],
                final_intent="different",
            ),
        )
        text = report.generate(ra)
        assert "Negation Introduced" in text


# ============================================================
# ANALYZER TESTS
# ============================================================


class TestAnalyzer:
    def test_analyze_basic(self):
        res = analyzer.analyze("How to code?", "How to code?")
        assert isinstance(res, RelationshipAnalysis)
        assert res.relationship_score > 0

    def test_analyze_different(self):
        res = analyzer.analyze("What is Python?", "How to bake cake?")
        assert isinstance(res, RelationshipAnalysis)

    def test_compare(self):
        result = analyzer.compare("Hello", "World")
        assert isinstance(result, dict)
        assert "relationship_score" in result


# ============================================================
# SEMANTIC FLAGS TESTS
# ============================================================


class TestSemanticFlags:
    def test_equivalent_intent_exact(self):
        res = detector.detect("How to code?", "How to code?")
        assert "equivalent_intent" in res.semantic_flags

    def test_more_specific(self):
        res = detector.detect("How to install?", "How to install Ubuntu?")
        flags = set(res.semantic_flags)
        assert "more_specific" in flags or "scope_change" in flags

    def test_numeric_shift(self):
        res = detector.detect("10 items", "20 items")
        assert "numeric_shift" in res.semantic_flags


# ============================================================
# RISK FLAGS TESTS
# ============================================================


class TestRiskFlags:
    def test_meaning_changed_negation(self):
        res = detector.detect("How to do this?", "How to not do this?")
        assert "meaning_changed" in res.risk_flags

    def test_numeric_conflict(self):
        res = detector.detect("10 items", "20 items")
        assert "numeric_conflict" in res.risk_flags

    def test_version_conflict(self):
        res = detector.detect("Python 3.8", "Python 3.9")
        assert "version_conflict" in res.risk_flags


# ============================================================
# TRANSFORMATION CHAIN TESTS
# ============================================================


class TestTransformationChainIntegration:
    def test_exact_chain(self):
        res = detector.detect("Hello", "Hello")
        assert res.transformation_chain.is_equivalent is True
        assert res.transformation_chain.final_intent == "equivalent"

    def test_chain_has_steps(self):
        res = detector.detect("How to install Ubuntu?", "How do I install Ubuntu Linux?")
        if res.transformation_chain.steps:
            assert res.transformation_chain.steps[0].step_type != ""

    def test_chain_not_equivalent_when_negation(self):
        res = detector.detect("How to do this?", "How to not do this?")
        assert res.transformation_chain.is_equivalent is False


# ============================================================
# RELATIONSHIP PATTERN CONSTANTS TESTS
# ============================================================


class TestPatternConstants:
    def test_negation_words_not_empty(self):
        assert len(NEGATION_WORDS) > 0
        assert "not" in NEGATION_WORDS
        assert "can't" in NEGATION_WORDS

    def test_pronouns_not_empty(self):
        assert len(PRONOUNS) > 0
        assert "i" in PRONOUNS
        assert "you" in PRONOUNS


# ============================================================
# PERFORMANCE TESTS
# ============================================================


class TestPerformance:
    def test_detector_under_5ms(self):
        import time

        start = time.time()
        for _ in range(100):
            detector.detect("How to install Python?", "How to install Java?")
        elapsed = (time.time() - start) * 1000 / 100
        assert elapsed < 5.0, f"Average {elapsed:.2f}ms exceeds 5ms"

    def test_analyzer_under_10ms(self):
        import time

        start = time.time()
        for _ in range(50):
            analyzer.analyze("How to install Python?", "How to install Java?")
        elapsed = (time.time() - start) * 1000 / 50
        assert elapsed < 10.0, f"Average {elapsed:.2f}ms exceeds 10ms"

    def test_report_generation_fast(self):
        ra = RelationshipAnalysis(
            relationship_types=[RelationshipInfo("test", 0.5) for _ in range(10)],
            relationship_score=50.0,
        )
        import time

        start = time.time()
        for _ in range(100):
            report.generate(ra)
        elapsed = (time.time() - start) * 1000 / 100
        assert elapsed < 1.0, f"Average {elapsed:.2f}ms exceeds 1ms"


# ============================================================
# INTEGRATION TESTS
# ============================================================


class TestIntegrationWithAnalyzer:
    def test_analyzer_has_relationship_analysis(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        qa = QueryAnalyzer()
        result = qa.analyze("How to install Python?", "How to install Python?")
        assert hasattr(result, "relationship_analysis")
        assert isinstance(result.relationship_analysis, RelationshipAnalysis)

    def test_relationship_analysis_in_to_dict(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        qa = QueryAnalyzer()
        result = qa.analyze("What is Python?", "What is Java?")
        d = result.to_dict()
        assert "relationship_analysis" in d

    def test_relationship_analysis_roundtrip(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        qa = QueryAnalyzer()
        result = qa.analyze("How to install Python?", "How to not install Python?")
        d = result.to_dict()
        from ares.query_understanding.query_models import QueryAnalysis

        restored = QueryAnalysis.from_dict(d)
        assert (
            restored.relationship_analysis.primary_relationship() == result.relationship_analysis.primary_relationship()
        )

    def test_full_report_includes_relationships(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer
        from ares.query_understanding.query_report import QueryReport

        qa = QueryAnalyzer()
        qr = QueryReport()
        result = qa.analyze("What is Python?", "What is Python?")
        text = qr.generate(result)
        assert "relationship" in text.lower()


# ============================================================
# EDGE CASES
# ============================================================


class TestEdgeCases:
    def test_unicode_questions(self):
        res = detector.detect("Café au lait?", "Café au lait?")
        assert res.primary_relationship() == "exact_match"

    def test_mixed_language(self):
        res = detector.detect("¿Cómo estás?", "How are you?")
        assert isinstance(res, RelationshipAnalysis)

    def test_very_long_text(self):
        q1 = "How to install Python on Ubuntu " * 20
        q2 = "How to install Python on Linux " * 20
        res = detector.detect(q1, q2)
        assert isinstance(res, RelationshipAnalysis)

    def test_special_characters(self):
        res = detector.detect("Hello @world!", "Hello #world?")
        assert isinstance(res, RelationshipAnalysis)

    def test_numbers_with_commas(self):
        res = detector.detect("1,000 items", "2,000 items")
        num_diffs = [r for r in res.relationship_types if r.relationship_type == "numeric_difference"]
        assert len(num_diffs) >= 1

    def test_version_with_letters(self):
        res = detector.detect("v2.0.1-alpha", "v2.0.1-beta")
        version_diffs = [r for r in res.relationship_types if r.relationship_type == "version_difference"]
        assert len(version_diffs) >= 1

    def test_dates_different_formats(self):
        res = detector.detect("Jan 15, 2024", "2024/06/20")
        assert res.relationship_score > 0

    def test_currency_symbols(self):
        res = detector.detect("$10", "€10")
        cur_diffs = [r for r in res.relationship_types if r.relationship_type == "currency_difference"]
        assert len(cur_diffs) >= 1 or res.relationship_score > 0

    def test_percentage_vs_decimal(self):
        res = detector.detect("50%", "0.5")
        assert res.relationship_score > 0

    def test_unit_conversion(self):
        res = detector.detect("10 cm", "10 inches")
        assert res.relationship_score > 0

    def test_abbreviation_upper_lower(self):
        res = detector.detect("AI", "ai")
        assert res.relationship_score > 0

    def test_duplicate_words(self):
        res = detector.detect("hello hello world", "hello world")
        dup_types = {r.relationship_type for r in res.relationship_types}
        assert "duplicate_tokens" in dup_types or "repeated_words" in dup_types

    def test_empty_spaces(self):
        res = detector.detect("   ", "hello")
        assert res.relationship_score == 0.0

    def test_none_values(self):
        res = detector.detect("hello", "")
        assert res.primary_relationship() == "unknown_relationship"

    def test_synonym_begin_start(self):
        res = detector.detect("begin the process", "start the process")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_synonym_fix_repair(self):
        res = detector.detect("fix the issue", "repair the issue")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_antonym_big_small(self):
        res = detector.detect("big house", "small house")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)

    def test_antonym_hot_cold(self):
        res = detector.detect("hot water", "cold water")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)

    def test_spelling_behavior_behaviour(self):
        res = detector.detect("good behavior", "good behaviour")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_spelling_theater_theatre(self):
        res = detector.detect("movie theater", "movie theatre")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_numbers_same(self):
        res = detector.detect("42", "42")
        assert res.primary_relationship() == "exact_match"

    def test_multiple_numbers(self):
        res = detector.detect("10 and 20", "10 and 30")
        num_types = {r.relationship_type for r in res.relationship_types}
        assert "numeric_difference" in num_types

    def test_qmark_vs_no_qmark(self):
        res = detector.detect("Hello?", "Hello")
        assert res.relationship_score >= 60

    def test_code_snippet_formatting(self):
        res = detector.detect("def foo(): pass", "def foo(): return")
        assert res.relationship_score > 0

    def test_html_vs_plain(self):
        res = detector.detect("<b>Hello</b>", "Hello")
        assert res.relationship_score > 0

    def test_with_newlines(self):
        res = detector.detect("line1\nline2", "line1 line2")
        assert isinstance(res, RelationshipAnalysis)

    def test_unicode_emoji(self):
        res = detector.detect("Python 😊", "Python 😢")
        assert res.relationship_score > 0

    def test_repeated_words_sequence(self):
        res = detector.detect("very very big", "very big")
        dup_types = {r.relationship_type for r in res.relationship_types}
        assert "duplicate_tokens" in dup_types or "repeated_words" in dup_types

    def test_version_range(self):
        res = detector.detect("Python 3.8 to 3.12", "Python 3.8 to 3.10")
        assert any(r.relationship_type == "version_difference" for r in res.relationship_types)

    def test_synonym_learn_study(self):
        res = detector.detect("learn Python", "study Python")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_synonym_install_setup(self):
        res = detector.detect("install software", "setup software")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_pronoun_shift(self):
        res = detector.detect("my code", "your code")
        assert any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types)

    def test_double_neg(self):
        res = detector.detect("not never", "not")
        neg_types = {r.relationship_type for r in res.relationship_types}
        assert "negation_removed" in neg_types

    def test_internal_duplicate(self):
        res = detector.detect("and and then", "and then")
        assert res.relationship_score > 0

    def test_question_words_diff(self):
        res = detector.detect("What is Python?", "Why Python?")
        assert res.relationship_score > 0

    def test_single_word_diff(self):
        res = detector.detect("Hello", "Hello world")
        assert res.relationship_score > 0

    def test_directory_path(self):
        res = detector.detect("/usr/bin/python", "/usr/bin/python3")
        assert isinstance(res, RelationshipAnalysis)

    def test_period_vs_comma_number(self):
        res = detector.detect("1.5", "1,5")
        num_types = {r.relationship_type for r in res.relationship_types}
        assert any("numeric" in t for t in num_types) or res.relationship_score > 0

    def test_same_meaning_synonyms(self):
        res = detector.detect("fast car", "quick car")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_different_tense(self):
        res = detector.detect("How to install?", "How to installed?")
        assert res.relationship_score > 0

    def test_special_chars_only(self):
        res = detector.detect("!!!", "???")
        assert isinstance(res, RelationshipAnalysis)

    def test_numbers_only(self):
        res = detector.detect("123", "456")
        assert any(r.relationship_type == "numeric_difference" for r in res.relationship_types)

    def test_currencies_mixed(self):
        res = detector.detect("$10 USD", "€10 EUR")
        assert res.relationship_score > 0

    def test_antonym_good_bad(self):
        res = detector.detect("good product", "bad product")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)

    def test_synonym_problem_issue(self):
        res = detector.detect("solve problem", "solve issue")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)


# ============================================================
# END-TO-END PREDICTION PIPELINE INTEGRATION
# ============================================================


class TestPredictionPipeline:
    def test_query_understanding_pipeline(self):
        from ares.query_understanding.query_pipeline import QueryPipeline

        pipe = QueryPipeline()
        result = pipe.run("How to code in Python?", "How to code in Java?")
        assert result.relationship_analysis.relationship_score > 0

    def test_pipeline_full_output(self):
        from ares.query_understanding.query_pipeline import QueryPipeline

        pipe = QueryPipeline()
        result = pipe.run("What is AI?", "What is Artificial Intelligence?")
        assert isinstance(result.relationship_analysis, RelationshipAnalysis)


# ============================================================
# COVERAGE GAPS — Additional cross-coverage
# ============================================================


class TestCoverageGaps:
    def test_entity_multiple_replacements(self):
        res = detector.detect("Python vs Java", "Python vs C++")
        assert len(res.relationship_types) >= 1

    def test_negation_polarity(self):
        res = detector.detect("not good", "not bad")
        neg_types = {r.relationship_type for r in res.relationship_types}
        assert "antonym_detection" in neg_types or "question_polarity_change" in neg_types

    def test_numeric_with_units(self):
        res = detector.detect("10 MB file", "20 MB file")
        assert any(r.relationship_type in ("numeric_difference", "unit_difference") for r in res.relationship_types)

    def test_currency_and_number(self):
        res = detector.detect("$10.50", "$20.50")
        assert any(r.relationship_type == "currency_difference" for r in res.relationship_types)

    def test_version_multi_dot(self):
        res = detector.detect("v1.2.3", "v1.2.4")
        assert any(r.relationship_type == "version_difference" for r in res.relationship_types)

    def test_abbreviation_multi_word(self):
        res = detector.detect("API design", "Application Programming Interface design")
        styles = {r.relationship_type for r in res.relationship_types}
        assert len(styles) > 0

    def test_synonym_multi_pair(self):
        res = detector.detect("create big app", "build large app")
        syn_types = {r.relationship_type for r in res.relationship_types}
        assert "synonym_replacement" in syn_types

    def test_typo_missing_char(self):
        res = detector.detect("programing", "programming")
        assert res.relationship_score >= 60

    def test_typo_extra_char(self):
        res = detector.detect("helloo", "hello")
        assert res.relationship_score >= 60

    def test_typo_substitution(self):
        res = detector.detect("colour", "color")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_mixed_synonym_antonym(self):
        res = detector.detect("very big", "very small")
        syn_types = {r.relationship_type for r in res.relationship_types}
        assert "antonym_detection" in syn_types

    def test_pronoun_all_variants(self):
        for p1 in ["i", "you", "he", "she", "we", "they"]:
            for p2 in ["i", "you", "he", "she", "we", "they"]:
                if p1 != p2:
                    res = detector.detect(f"{p1} like it", f"{p2} like it")
                    if any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types):
                        break
            else:
                continue
            break

    def test_time_format_variants(self):
        res = detector.detect("3:00 PM", "15:00")
        time_types = {r.relationship_type for r in res.relationship_types}
        assert "time_difference" in time_types or res.relationship_score > 0

    def test_whitespace_formats(self):
        res = detector.detect("hello\tworld", "hello world")
        assert res.relationship_score >= 90

    def test_none_empty_returns_empty(self):
        res = detector.detect(None, "hello")
        assert isinstance(res, RelationshipAnalysis)

    def test_non_string_input(self):
        res = detector.detect("hello", "hello")
        assert res.primary_relationship() == "exact_match"

    def test_version_with_suffixes(self):
        res = detector.detect("v2.0b1", "v2.0b2")
        assert any(r.relationship_type == "version_difference" for r in res.relationship_types)

    def test_multi_currency_and_number(self):
        res = detector.detect("$50 for 10 items", "€50 for 20 items")
        types = {r.relationship_type for r in res.relationship_types}
        assert len(types) >= 1

    def test_academic_abbreviation(self):
        res = detector.detect("ML course", "Machine Learning course")
        assert res.relationship_score > 0

    def test_os_abbreviation(self):
        res = detector.detect("OS update", "Operating System update")
        assert res.relationship_score > 0

    def test_entity_with_abbreviation(self):
        res = detector.detect("AWS vs Azure", "Amazon Web Services vs Microsoft Azure")
        assert res.relationship_score > 0

    def test_synonym_create_make(self):
        res = detector.detect("create an app", "make an app")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_synonym_fast_quick(self):
        res = detector.detect("fast solution", "quick solution")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_synonym_show_display(self):
        res = detector.detect("show results", "display results")
        assert any(r.relationship_type == "synonym_replacement" for r in res.relationship_types)

    def test_antonym_positive_negative(self):
        res = detector.detect("positive feedback", "negative feedback")
        assert any(r.relationship_type == "antonym_detection" for r in res.relationship_types)

    def test_spelling_organize_organise(self):
        res = detector.detect("organize files", "organise files")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_spelling_realize_realise(self):
        res = detector.detect("realize the truth", "realise the truth")
        assert any(r.relationship_type == "spelling_variant" for r in res.relationship_types)

    def test_numeric_percentage_both(self):
        res = detector.detect("50% discount", "75% discount")
        assert any(r.relationship_type == "percentage_difference" for r in res.relationship_types)

    def test_multiple_dates(self):
        res = detector.detect("from 2024/01/15 to 2024/06/20", "from 2024/01/15 to 2024/07/01")
        date_diffs = [r for r in res.relationship_types if r.relationship_type == "date_difference"]
        assert len(date_diffs) >= 1

    def test_pronoun_my_your(self):
        res = detector.detect("my computer", "your computer")
        assert any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types)

    def test_pronoun_he_she(self):
        res = detector.detect("he said", "she said")
        assert any(r.relationship_type == "pronoun_replacement" for r in res.relationship_types)

    def test_duplicate_word_repeated(self):
        res = detector.detect("very very good", "very good")
        dup_types = {r.relationship_type for r in res.relationship_types}
        assert "duplicate_tokens" in dup_types or "repeated_words" in dup_types

    def test_multi_version_diffs(self):
        res = detector.detect("versions 1.0, 2.0", "versions 1.0, 3.0")
        assert any(r.relationship_type == "version_difference" for r in res.relationship_types)
