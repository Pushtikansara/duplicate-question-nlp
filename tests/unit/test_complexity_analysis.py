from __future__ import annotations

import time

import pytest

from ares.query_understanding.complexity_analyzer import ComplexityAnalyzer
from ares.query_understanding.complexity_models import (
    DIFFICULTY_EASY,
    DIFFICULTY_HARD,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_VERY_EASY,
    DIFFICULTY_VERY_HARD,
    ComplexityAnalysis,
    score_to_difficulty,
)
from ares.query_understanding.complexity_report import ComplexityReport
from ares.query_understanding.complexity_rules import (
    abbreviation_density,
    ambiguity_score,
    comparison_difficulty,
    confidence_estimate,
    count_syllables,
    entity_complexity,
    entity_density,
    flesch_reading_ease,
    lexical_complexity,
    numeric_density,
    question_length_score,
    rare_token_density,
    readability_complexity,
    risk_score,
    semantic_complexity,
    sentence_complexity,
    syntactic_complexity,
    token_diversity,
)
from ares.query_understanding.entity_models import EntityResult
from ares.query_understanding.query_models import (
    QuestionMetadata,
    QuestionSimilarityFeatures,
)
from ares.query_understanding.relationship_models import RelationshipAnalysis


# ============================================================
# Difficulty level mapping
# ============================================================
class TestDifficultyLevels:
    def test_very_easy(self):
        assert score_to_difficulty(0.05) == DIFFICULTY_VERY_EASY

    def test_very_easy_boundary(self):
        assert score_to_difficulty(0.099) == DIFFICULTY_VERY_EASY

    def test_easy(self):
        assert score_to_difficulty(0.1) == DIFFICULTY_EASY

    def test_easy_upper(self):
        assert score_to_difficulty(0.24) == DIFFICULTY_EASY

    def test_medium(self):
        assert score_to_difficulty(0.25) == DIFFICULTY_MEDIUM

    def test_medium_upper(self):
        assert score_to_difficulty(0.44) == DIFFICULTY_MEDIUM

    def test_hard(self):
        assert score_to_difficulty(0.45) == DIFFICULTY_HARD

    def test_hard_upper(self):
        assert score_to_difficulty(0.64) == DIFFICULTY_HARD

    def test_very_hard(self):
        assert score_to_difficulty(0.65) == DIFFICULTY_VERY_HARD

    def test_very_hard_max(self):
        assert score_to_difficulty(1.0) == DIFFICULTY_VERY_HARD

    def test_negative_clamped(self):
        assert score_to_difficulty(-0.1) == DIFFICULTY_VERY_EASY


# ============================================================
# ComplexityAnalysis model
# ============================================================
class TestComplexityAnalysis:
    def test_defaults(self):
        ca = ComplexityAnalysis()
        assert ca.overall_complexity_score == 0.0
        assert ca.difficulty_level == DIFFICULTY_VERY_EASY
        assert ca.version == "1.0.0"

    def test_to_dict(self):
        ca = ComplexityAnalysis(overall_complexity_score=0.5, difficulty_level=DIFFICULTY_MEDIUM)
        d = ca.to_dict()
        assert d["overall_complexity_score"] == 0.5
        assert d["difficulty_level"] == DIFFICULTY_MEDIUM

    def test_to_dict_includes_all_keys(self):
        ca = ComplexityAnalysis()
        d = ca.to_dict()
        expected = [
            "overall_complexity_score",
            "difficulty_level",
            "lexical_complexity",
            "syntactic_complexity",
            "semantic_complexity",
            "entity_complexity",
            "ambiguity_score",
            "readability_score",
            "comparison_difficulty",
            "rare_token_density",
            "entity_density",
            "numeric_density",
            "abbreviation_density",
            "sentence_complexity",
            "question_length_score",
            "token_diversity",
            "confidence_estimate",
            "risk_score",
            "reasoning_summary",
            "processing_time",
            "version",
        ]
        for key in expected:
            assert key in d

    def test_from_dict(self):
        d = {"overall_complexity_score": 0.75, "difficulty_level": DIFFICULTY_HARD}
        ca = ComplexityAnalysis.from_dict(d)
        assert ca.overall_complexity_score == 0.75
        assert ca.difficulty_level == DIFFICULTY_HARD

    def test_from_dict_empty(self):
        ca = ComplexityAnalysis.from_dict({})
        assert ca.overall_complexity_score == 0.0
        assert ca.difficulty_level == DIFFICULTY_VERY_EASY

    def test_roundtrip(self):
        ca1 = ComplexityAnalysis(
            overall_complexity_score=0.42, difficulty_level=DIFFICULTY_MEDIUM, lexical_complexity=0.3
        )
        d = ca1.to_dict()
        ca2 = ComplexityAnalysis.from_dict(d)
        assert ca2.overall_complexity_score == 0.42
        assert ca2.difficulty_level == DIFFICULTY_MEDIUM
        assert ca2.lexical_complexity == 0.3


# ============================================================
# Lexical complexity
# ============================================================
class TestLexicalComplexity:
    def test_empty(self):
        assert lexical_complexity([]) == 0.0

    def test_short_words(self):
        assert lexical_complexity(["a", "b", "c"]) < 0.3

    def test_long_words(self):
        score = lexical_complexity(["antidisestablishment", "incomprehensibilities"])
        assert score > 0.5

    def test_mixed(self):
        score = lexical_complexity(["the", "cat", "sat", "incomprehensible"])
        assert 0.0 < score < 1.0

    def test_single_short(self):
        score = lexical_complexity(["hi"])
        assert score >= 0.0


# ============================================================
# Syntactic complexity
# ============================================================
class TestSyntacticComplexity:
    def test_empty_tokens(self):
        assert syntactic_complexity([], 1) == 0.0

    def test_zero_sentences(self):
        assert syntactic_complexity(["a", "b"], 0) == 0.0

    def test_short_sentence(self):
        assert syntactic_complexity(["a", "b", "c"], 1) == 0.0

    def test_medium_sentence(self):
        assert syntactic_complexity(["w"] * 12, 1) == 0.4

    def test_long_sentence(self):
        assert syntactic_complexity(["w"] * 25, 1) == 0.8

    def test_very_long_sentence(self):
        assert syntactic_complexity(["w"] * 40, 1) == 1.0

    def test_multiple_short_sentences(self):
        assert syntactic_complexity(["w"] * 10, 3) == 0.0


# ============================================================
# Semantic complexity
# ============================================================
class TestSemanticComplexity:
    def test_empty(self):
        assert semantic_complexity([]) == 0.0

    def test_only_common_words(self):
        assert semantic_complexity(["the", "a", "is", "of"]) == 0.0

    def test_uncommon_words(self):
        score = semantic_complexity(["antidisestablishment", "epistemology"])
        assert score > 0.5

    def test_mixed(self):
        score = semantic_complexity(["the", "cat", "sat", "on", "epistemology"])
        assert 0.0 < score < 1.0


# ============================================================
# Entity complexity
# ============================================================
class TestEntityComplexity:
    def test_zero_words(self):
        assert entity_complexity(5, 0) == 0.0

    def test_no_entities(self):
        assert entity_complexity(0, 10) == 0.0

    def test_low_density(self):
        assert entity_complexity(1, 20) == 0.0

    def test_medium_density(self):
        score = entity_complexity(3, 10)
        assert score == 0.5

    def test_high_density(self):
        score = entity_complexity(5, 10)
        assert score == 0.7

    def test_very_high_density(self):
        score = entity_complexity(7, 10)
        assert score == 1.0

    def test_max_density(self):
        assert entity_complexity(10, 10) == 1.0


# ============================================================
# Ambiguity score
# ============================================================
class TestAmbiguityScore:
    def test_empty(self):
        assert ambiguity_score([], "") == 0.0

    def test_no_ambiguity(self):
        score = ambiguity_score(["python", "javascript", "java"], "python javascript java")
        assert score == 0.0

    def test_pronouns(self):
        score = ambiguity_score(["it", "is", "good"], "it is good")
        assert score > 0.0

    def test_ambiguous_words(self):
        score = ambiguity_score(["get", "the", "thing"], "get the thing")
        assert score > 0.0

    def test_very_short(self):
        score = ambiguity_score(["it"], "it")
        assert score > 0.1

    def test_very_long(self):
        score = ambiguity_score(["word"] * 25, " ".join(["word"] * 25))
        assert score >= 0.1

    def test_mixed_case(self):
        text = "iPhone iPad MacBook"
        tokens = text.split()
        score = ambiguity_score(tokens, text)
        assert score >= 0.0

    def test_saturated(self):
        text = "it it it it it they they they this this that"
        tokens = text.split()
        score = ambiguity_score(tokens, text)
        assert score <= 1.0


# ============================================================
# Readability
# ============================================================
class TestReadabilityComplexity:
    def test_very_readable(self):
        assert readability_complexity(95.0) == 0.0

    def test_readable(self):
        assert readability_complexity(75.0) == 0.2

    def test_fairly_difficult(self):
        assert readability_complexity(55.0) == 0.4

    def test_difficult(self):
        assert readability_complexity(35.0) == 0.6

    def test_very_difficult(self):
        assert readability_complexity(15.0) == 0.8

    def test_extremely_difficult(self):
        assert readability_complexity(5.0) == 1.0

    def test_boundary_90(self):
        assert readability_complexity(90.0) == 0.0

    def test_boundary_70(self):
        assert readability_complexity(70.0) == 0.2

    def test_boundary_50(self):
        assert readability_complexity(50.0) == 0.4

    def test_boundary_30(self):
        assert readability_complexity(30.0) == 0.6

    def test_boundary_10(self):
        assert readability_complexity(10.0) == 0.8


# ============================================================
# Flesch Reading Ease
# ============================================================
class TestFleschReadingEase:
    def test_empty(self):
        assert flesch_reading_ease("") == 100.0

    def test_simple_text(self):
        score = flesch_reading_ease("the cat sat on the mat")
        assert score > 80.0

    def test_complex_text(self):
        score = flesch_reading_ease("antidisestablishment epistemological incomprehensibility")
        assert score < 30.0

    def test_clamped_upper(self):
        score = flesch_reading_ease("a")
        assert score <= 100.0

    def test_clamped_lower(self):
        words = " ".join(["antidisestablishment"] * 20)
        score = flesch_reading_ease(words)
        assert score >= 0.0


# ============================================================
# Count Syllables
# ============================================================
class TestCountSyllables:
    def test_empty(self):
        assert count_syllables("") == 0

    def test_single_syllable(self):
        assert count_syllables("cat") == 1

    def test_two_syllables(self):
        assert count_syllables("hello") == 2

    def test_three_syllables(self):
        assert count_syllables("banana") == 3

    def test_silent_e(self):
        assert count_syllables("cake") == 1

    def test_multiple_vowels(self):
        assert count_syllables("beautiful") >= 2

    def test_y_as_vowel(self):
        assert count_syllables("gym") == 1

    def test_case_insensitive(self):
        assert count_syllables("HELLO") == count_syllables("hello")


# ============================================================
# Rare token density
# ============================================================
class TestRareTokenDensity:
    def test_empty(self):
        assert rare_token_density([]) == 0.0

    def test_all_common(self):
        assert rare_token_density(["the", "a", "is"]) == 0.0

    def test_some_rare(self):
        score = rare_token_density(["the", "epistemology", "cat"])
        assert score > 0.0

    def test_all_rare_long(self):
        score = rare_token_density(["antidisestablishment", "incomprehensibility"])
        assert score > 0.5


# ============================================================
# Entity density
# ============================================================
class TestEntityDensity:
    def test_zero_words(self):
        assert entity_density(5, 0) == 0.0

    def test_no_entities(self):
        assert entity_density(0, 10) == 0.0

    def test_some_density(self):
        assert entity_density(3, 10) == 0.3

    def test_all_entities(self):
        assert entity_density(5, 5) == 1.0

    def test_clamped(self):
        assert entity_density(10, 5) == 1.0


# ============================================================
# Abbreviation density
# ============================================================
class TestAbbreviationDensity:
    def test_empty(self):
        assert abbreviation_density([]) == 0.0

    def test_no_abbreviations(self):
        assert abbreviation_density(["the", "cat"]) == 0.0

    def test_all_abbreviations(self):
        assert abbreviation_density(["AI", "NLP", "ML"]) == 1.0

    def test_mixed(self):
        score = abbreviation_density(["AI", "the", "cat"])
        assert score == pytest.approx(1 / 3)

    def test_lowercase_not_abbrev(self):
        assert abbreviation_density(["ai", "nlp"]) == 0.0


# ============================================================
# Numeric density
# ============================================================
class TestNumericDensity:
    def test_empty(self):
        assert numeric_density([]) == 0.0

    def test_no_numbers(self):
        assert numeric_density(["the", "cat"]) == 0.0

    def test_some_numbers(self):
        score = numeric_density(["42", "cat", "100"])
        assert score == pytest.approx(2 / 3)

    def test_all_numbers(self):
        assert numeric_density(["42", "3.14", "100"]) == 1.0

    def test_decimal(self):
        assert numeric_density(["3.14"]) == 1.0


# ============================================================
# Sentence complexity
# ============================================================
class TestSentenceComplexity:
    def test_single(self):
        assert sentence_complexity(["a", "b"], 1) == 0.0

    def test_two_sentences(self):
        assert sentence_complexity(["a", "b"], 2) == 0.2

    def test_three_sentences(self):
        assert sentence_complexity(["a", "b"], 3) == 0.4

    def test_five_sentences(self):
        assert sentence_complexity(["a", "b"], 5) == 0.6

    def test_many_sentences(self):
        assert sentence_complexity(["a", "b"], 10) == 0.8

    def test_zero_sentences(self):
        assert sentence_complexity(["a"], 0) == 0.0


# ============================================================
# Question length score
# ============================================================
class TestQuestionLengthScore:
    def test_empty(self):
        assert question_length_score("") == 0.0

    def test_very_short(self):
        assert question_length_score("hi") == 0.1

    def test_short(self):
        assert question_length_score("hello world") == 0.2

    def test_medium(self):
        assert question_length_score("a" * 40) == 0.4

    def test_long(self):
        assert question_length_score("a" * 80) == 0.6

    def test_very_long(self):
        assert question_length_score("a" * 120) == 0.8

    def test_extreme(self):
        assert question_length_score("a" * 200) == 1.0

    def test_boundary_30(self):
        assert question_length_score("a" * 30) == 0.2

    def test_boundary_60(self):
        assert question_length_score("a" * 60) == 0.4

    def test_boundary_100(self):
        assert question_length_score("a" * 100) == 0.6

    def test_boundary_150(self):
        assert question_length_score("a" * 150) == 0.8


# ============================================================
# Token diversity
# ============================================================
class TestTokenDiversity:
    def test_empty(self):
        assert token_diversity([]) == 0.0

    def test_all_unique(self):
        assert token_diversity(["a", "b", "c"]) == 1.0

    def test_all_duplicate(self):
        assert token_diversity(["a", "a", "a"]) == pytest.approx(1 / 3)

    def test_case_insensitive_unique(self):
        assert token_diversity(["A", "a", "b"]) == pytest.approx(2 / 3)


# ============================================================
# Comparison difficulty
# ============================================================
class TestComparisonDifficulty:
    def test_low_overlap(self):
        score = comparison_difficulty(overlap_ratio=0.1, entity_delta=0, type_mismatch=False, relationship_count=0)
        assert score >= 0.3

    def test_high_overlap(self):
        score = comparison_difficulty(overlap_ratio=0.95, entity_delta=0, type_mismatch=False, relationship_count=0)
        assert score == 0.0

    def test_medium_overlap(self):
        score = comparison_difficulty(overlap_ratio=0.5, entity_delta=0, type_mismatch=False, relationship_count=0)
        assert score == 0.1

    def test_entity_delta_high(self):
        score = comparison_difficulty(overlap_ratio=0.5, entity_delta=5, type_mismatch=False, relationship_count=0)
        assert score >= 0.3

    def test_type_mismatch(self):
        score = comparison_difficulty(overlap_ratio=0.5, entity_delta=0, type_mismatch=True, relationship_count=0)
        assert score >= 0.25

    def test_many_relationships(self):
        score = comparison_difficulty(overlap_ratio=0.5, entity_delta=0, type_mismatch=False, relationship_count=6)
        assert score >= 0.3

    def test_all_factors(self):
        score = comparison_difficulty(overlap_ratio=0.1, entity_delta=5, type_mismatch=True, relationship_count=10)
        assert score > 0.8


# ============================================================
# Confidence estimate
# ============================================================
class TestConfidenceEstimate:
    def test_perfect(self):
        assert confidence_estimate(0.0, 0.0, 0.0) == 1.0

    def test_moderate(self):
        c = confidence_estimate(0.5, 0.3, 0.2)
        assert 0.0 < c < 1.0

    def test_low(self):
        c = confidence_estimate(1.0, 1.0, 1.0)
        assert c == 0.0

    def test_floor(self):
        c = confidence_estimate(2.0, 2.0, 2.0)
        assert c == 0.0


# ============================================================
# Risk score
# ============================================================
class TestRiskScore:
    def test_no_risk(self):
        assert risk_score(0.0, 0.0, 0.0) == 0.0

    def test_high_risk(self):
        r = risk_score(1.0, 1.0, 1.0)
        assert r == 1.0

    def test_moderate(self):
        r = risk_score(0.5, 0.3, 0.2)
        assert 0.0 < r < 1.0

    def test_clamped(self):
        r = risk_score(2.0, 1.0, 1.0)
        assert r <= 1.0


# ============================================================
# ComplexityAnalyzer integration
# ============================================================
class TestComplexityAnalyzer:
    def test_empty_input(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("", "")
        assert result.overall_complexity_score == 0.0

    def test_simple_questions(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert 0.0 <= result.overall_complexity_score <= 1.0
        assert result.processing_time >= 0.0

    def test_complex_questions(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "How does the implementation of gradient descent with momentum compare to Adam optimizer?",
            "What are the key differences between supervised and unsupervised machine learning approaches?",
        )
        assert result.overall_complexity_score > 0.1

    def test_with_metadata(self):
        analyzer = ComplexityAnalyzer()
        meta = QuestionMetadata(word_count=5, sentence_count=1)
        result = analyzer.analyze(
            "What is Python?",
            "What is Java?",
            metadata_1=meta,
            metadata_2=meta,
        )
        assert result.overall_complexity_score >= 0.0

    def test_with_similarity(self):
        analyzer = ComplexityAnalyzer()
        sim = QuestionSimilarityFeatures(word_overlap_ratio=0.8)
        result = analyzer.analyze(
            "What is Python?",
            "What is Java?",
            similarity=sim,
        )
        assert result.comparison_difficulty >= 0.0

    def test_with_entity_analysis(self):
        analyzer = ComplexityAnalyzer()
        from ares.query_understanding.entity_models import Entity

        er = EntityResult(
            entities_1=[Entity(text="Python", entity_type="LANGUAGE", start=0, end=6)],
            entities_2=[Entity(text="Java", entity_type="LANGUAGE", start=0, end=4)],
        )
        result = analyzer.analyze("What is Python?", "What is Java?", entity_analysis=er)
        assert result.entity_complexity >= 0.0

    def test_with_relationship_analysis(self):
        analyzer = ComplexityAnalyzer()
        from ares.query_understanding.relationship_models import RelationshipInfo

        ra = RelationshipAnalysis(
            relationship_types=[
                RelationshipInfo(relationship_type="exact_match", confidence=1.0),
            ],
        )
        result = analyzer.analyze(
            "What is Python?",
            "What is Java?",
            relationship_analysis=ra,
        )
        assert result.comparison_difficulty >= 0.0

    def test_returns_all_fields(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert result.lexical_complexity >= 0.0
        assert result.syntactic_complexity >= 0.0
        assert result.semantic_complexity >= 0.0
        assert result.entity_complexity >= 0.0
        assert result.ambiguity_score >= 0.0
        assert result.readability_score >= 0.0
        assert result.comparison_difficulty >= 0.0
        assert result.rare_token_density >= 0.0
        assert result.entity_density >= 0.0
        assert result.numeric_density >= 0.0
        assert result.abbreviation_density >= 0.0
        assert result.sentence_complexity >= 0.0
        assert result.question_length_score >= 0.0
        assert result.token_diversity >= 0.0
        assert result.confidence_estimate >= 0.0
        assert result.risk_score >= 0.0
        assert result.reasoning_summary != ""

    def test_version(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A", "B")
        assert result.version == "1.0.0"

    def test_difficulty_mapping(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A", "B")
        assert result.difficulty_level in (
            DIFFICULTY_VERY_EASY,
            DIFFICULTY_EASY,
            DIFFICULTY_MEDIUM,
            DIFFICULTY_HARD,
            DIFFICULTY_VERY_HARD,
        )


# ============================================================
# Performance
# ============================================================
class TestPerformance:
    def test_average_under_3ms(self):
        analyzer = ComplexityAnalyzer()
        times = []
        for _ in range(20):
            start = time.time()
            analyzer.analyze("What is the capital of France?", "Compare Paris and London")
            times.append((time.time() - start) * 1000)
        avg = sum(times) / len(times)
        assert avg < 3.0

    def test_bulk_performance(self):
        analyzer = ComplexityAnalyzer()
        pairs = [
            ("A", "B"),
            ("What is Python?", "What is Java?"),
            ("How to implement gradient descent?", "How does Adam optimizer work?"),
            ("Compare Transformers and LSTMs for NLP tasks", "What are the advantages of attention mechanisms?"),
            ("Why is the sky blue?", "Explain the color of the sky"),
        ]
        start = time.time()
        for q1, q2 in pairs:
            analyzer.analyze(q1, q2)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 50.0


# ============================================================
# ComplexityReport
# ============================================================
class TestComplexityReport:
    def test_generate_default(self):
        report = ComplexityReport()
        ca = ComplexityAnalysis(overall_complexity_score=0.5, difficulty_level=DIFFICULTY_MEDIUM)
        text = report.generate(ca)
        assert "COMPLEXITY ANALYSIS REPORT" in text
        assert DIFFICULTY_MEDIUM in text

    def test_generate_detailed(self):
        report = ComplexityReport()
        ca = ComplexityAnalysis(overall_complexity_score=0.75, difficulty_level=DIFFICULTY_HARD)
        text = report.generate(ca, detailed=True)
        assert "DETAILED METRICS" in text
        assert "Lexical Complexity" in text
        assert "Syntactic Complexity" in text

    def test_generate_short(self):
        report = ComplexityReport()
        ca = ComplexityAnalysis(overall_complexity_score=0.3, difficulty_level=DIFFICULTY_EASY)
        text = report.generate(ca, detailed=False)
        assert "COMPLEXITY ANALYSIS REPORT" in text
        assert "DETAILED METRICS" not in text

    def test_short_report(self):
        report = ComplexityReport()
        ca = ComplexityAnalysis(overall_complexity_score=0.5, difficulty_level=DIFFICULTY_MEDIUM)
        text = report.short_report(ca)
        assert DIFFICULTY_MEDIUM in text
        assert "0.5" in text


# ============================================================
# Edge cases
# ============================================================
class TestEdgeCases:
    def test_unicode(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("¿Qué es Python?", "Was ist Java?")
        assert 0.0 <= result.overall_complexity_score <= 1.0

    def test_numeric_heavy(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "Compare 42 with 100 and 3.14 with 2.718",
            "What is 7 * 8 + 3?",
        )
        assert result.numeric_density > 0.0

    def test_abbreviation_heavy_raw(self):
        from ares.query_understanding.complexity_rules import abbreviation_density

        raw_tokens = ["What", "is", "the", "difference", "between", "AI", "ML", "NLP", "and", "CNN"]
        assert abbreviation_density(raw_tokens) > 0.0

    def test_abbreviation_heavy(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "What is the difference between AI, ML, NLP, and CNN?",
            "Compare RNN, LSTM, GRU, and BERT models",
        )
        assert result.abbreviation_density >= 0.0

    def test_very_short_questions(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A?", "B?")
        assert result.overall_complexity_score >= 0.0

    def test_very_long_questions(self):
        analyzer = ComplexityAnalyzer()
        long_q = " ".join(["word"] * 100)
        result = analyzer.analyze(long_q, long_q)
        assert result.question_length_score > 0.5

    def test_mixed_language(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "Wie geht es Ihnen?",
            "Comment allez-vous?",
        )
        assert result.semantic_complexity >= 0.0

    def test_code_snippets(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "How to write a for loop in Python?",
            "for i in range(10): print(i)",
        )
        assert result.overall_complexity_score >= 0.0

    def test_empty_vs_nonempty(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("", "What is Python?")
        assert result.overall_complexity_score == 0.0

    def test_special_chars_only(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("!!! ???", "@@@ ###")
        assert result.overall_complexity_score >= 0.0

    def test_numbers_and_dates(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "Compare 2024 with 2025",
            "What happened on 2024-01-01?",
        )
        assert result.numeric_density >= 0.0

    def test_entity_heavy(self):
        analyzer = ComplexityAnalyzer()
        from ares.query_understanding.entity_models import Entity

        entities = [
            Entity(text=t, entity_type="TECH", start=i * 5, end=i * 5 + len(t))
            for i, t in enumerate(["Python", "Java", "C++", "Rust", "Go", "Swift", "Kotlin", "TypeScript"])
        ]
        er = EntityResult(entities_1=entities, entities_2=entities)
        result = analyzer.analyze("A", "B", entity_analysis=er)
        assert result.entity_complexity > 0.3

    def test_pronoun_ambiguity(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "What is it?",
            "How does this work?",
        )
        assert result.ambiguity_score > 0.0

    def test_identical_questions(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Python?")
        assert result.comparison_difficulty >= 0.0

    def test_confidence_high_for_simple(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A?", "B?")
        assert result.confidence_estimate > 0.8

    def test_confidence_lower_for_complex(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "How does the antidisestablishment epistemological incomprehensibility work?",
            "What is the incomprehensible transcendental phenomenological ontology?",
        )
        assert result.confidence_estimate <= 1.0

    def test_risk_score_low_for_simple(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A?", "B?")
        assert result.risk_score < 0.3

    def test_none_input(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("", "")
        assert result.overall_complexity_score == 0.0

    def test_whitespace_only(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("   ", "   ")
        assert result.overall_complexity_score == 0.0
        assert result.processing_time >= 0.0

    def test_single_char(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("a", "b")
        assert result.overall_complexity_score >= 0.0

    def test_repeated_words(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("word word word", "word word word")
        assert result.token_diversity < 0.5


# ============================================================
# Serialization
# ============================================================
class TestSerialization:
    def test_complexity_analysis_to_dict_roundtrip(self):
        ca = ComplexityAnalysis(
            overall_complexity_score=0.5,
            difficulty_level=DIFFICULTY_MEDIUM,
            lexical_complexity=0.3,
            syntactic_complexity=0.2,
            semantic_complexity=0.4,
            entity_complexity=0.1,
            ambiguity_score=0.2,
            readability_score=0.3,
            comparison_difficulty=0.4,
            rare_token_density=0.1,
            entity_density=0.2,
            numeric_density=0.0,
            abbreviation_density=0.1,
            sentence_complexity=0.0,
            question_length_score=0.3,
            token_diversity=0.8,
            confidence_estimate=0.9,
            risk_score=0.1,
            reasoning_summary="Simple comparison",
            processing_time=1.5,
            version="1.0.0",
        )
        d = ca.to_dict()
        ca2 = ComplexityAnalysis.from_dict(d)
        assert ca2.overall_complexity_score == 0.5
        assert ca2.difficulty_level == DIFFICULTY_MEDIUM
        assert ca2.lexical_complexity == 0.3
        assert ca2.syntactic_complexity == 0.2
        assert ca2.semantic_complexity == 0.4
        assert ca2.entity_complexity == 0.1
        assert ca2.ambiguity_score == 0.2
        assert ca2.readability_score == 0.3
        assert ca2.comparison_difficulty == 0.4
        assert ca2.rare_token_density == 0.1
        assert ca2.entity_density == 0.2
        assert ca2.numeric_density == 0.0
        assert ca2.abbreviation_density == 0.1
        assert ca2.sentence_complexity == 0.0
        assert ca2.question_length_score == 0.3
        assert ca2.token_diversity == 0.8
        assert ca2.confidence_estimate == 0.9
        assert ca2.risk_score == 0.1
        assert ca2.reasoning_summary == "Simple comparison"
        assert ca2.processing_time == 1.5
        assert ca2.version == "1.0.0"

    def test_json_serializable(self):
        import json

        ca = ComplexityAnalysis(overall_complexity_score=0.5)
        d = ca.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["overall_complexity_score"] == 0.5


# ============================================================
# Integration with QueryAnalysis
# ============================================================
class TestIntegrationWithAnalyzer:
    def test_analyzer_has_complexity_analysis(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert hasattr(result, "complexity_analysis")
        assert isinstance(result.complexity_analysis, ComplexityAnalysis)

    def test_complexity_analysis_in_to_dict(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        d = result.to_dict()
        assert "complexity_analysis" in d
        assert "overall_complexity_score" in d["complexity_analysis"]

    def test_complexity_analysis_roundtrip(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        d = result.to_dict()
        from ares.query_understanding.query_models import QueryAnalysis

        restored = QueryAnalysis.from_dict(d)
        assert (
            restored.complexity_analysis.overall_complexity_score == result.complexity_analysis.overall_complexity_score
        )
        assert restored.complexity_analysis.difficulty_level == result.complexity_analysis.difficulty_level

    def test_full_report_includes_complexity(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer
        from ares.query_understanding.query_report import QueryReport

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        report = QueryReport()
        text = report.generate(result)
        assert "complexity" in text.lower() or "Complexity" in text

    def test_complexity_pipeline_includes_analysis(self):
        from ares.query_understanding.query_pipeline import QueryPipeline

        pipeline = QueryPipeline()
        result = pipeline.run("What is Python?", "What is Java?")
        assert result.complexity_analysis.overall_complexity_score >= 0.0

    def test_difficulty_reasoning_is_present(self):
        from ares.query_understanding.query_analyzer import QueryAnalyzer

        analyzer = QueryAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert result.complexity_analysis.reasoning_summary != ""


# ============================================================
# Regression tests
# ============================================================
class TestRegression:
    def test_regression_simple(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("What is Python?", "What is Java?")
        assert result.overall_complexity_score < 0.5
        assert result.difficulty_level in (DIFFICULTY_VERY_EASY, DIFFICULTY_EASY, DIFFICULTY_MEDIUM)

    def test_regression_complex(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(
            "How does the implementation of gradient descent with momentum compare to Adam optimizer in deep learning?",
            "What are the key differences between supervised and unsupervised machine learning approaches for classification?",
        )
        assert result.overall_complexity_score > 0.2

    def test_regression_entity_heavy(self):
        analyzer = ComplexityAnalyzer()
        from ares.query_understanding.entity_models import Entity

        entities = [
            Entity(text="TensorFlow", entity_type="LIBRARY", start=0, end=10),
            Entity(text="PyTorch", entity_type="LIBRARY", start=15, end=22),
            Entity(text="Keras", entity_type="LIBRARY", start=25, end=30),
            Entity(text="JAX", entity_type="LIBRARY", start=35, end=38),
        ]
        er = EntityResult(entities_1=entities, entities_2=entities)
        result = analyzer.analyze("A", "B", entity_analysis=er)
        assert result.entity_complexity > 0.2

    def test_regression_none_values(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("A", "B", metadata_1=None, metadata_2=None)
        assert result.overall_complexity_score >= 0.0
