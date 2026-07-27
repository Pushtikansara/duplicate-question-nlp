from __future__ import annotations

import json

import pytest

from ares.query_understanding.query_analyzer import QueryAnalyzer
from ares.query_understanding.query_features import (
    extract_complexity,
    extract_question_metadata,
    extract_readability,
    extract_sentence_statistics,
    extract_similarity_features,
    extract_token_statistics,
)
from ares.query_understanding.query_models import QueryAnalysis, QuestionMetadata
from ares.query_understanding.query_pipeline import QueryPipeline
from ares.query_understanding.query_report import QueryReport
from ares.query_understanding.utils import (
    contains_code,
    contains_date,
    contains_email,
    contains_emoji,
    contains_url,
    count_syllables,
    detect_language,
    flesch_reading_ease,
    is_question,
    jaccard_similarity,
    normalize_text,
    sentencize,
    tokenize,
    validate_input,
)

analyzer = QueryAnalyzer()
pipeline = QueryPipeline()
report = QueryReport()


class TestValidation:
    def test_empty_questions(self):
        with pytest.raises(ValueError):
            validate_input("", "")

    def test_non_string_input(self):
        with pytest.raises(TypeError):
            validate_input(123, "hello")

    def test_one_empty_valid(self):
        validate_input("hello", "")


class TestNormalization:
    def test_lowercase(self):
        assert normalize_text("Hello World") == "hello world"

    def test_strip_whitespace(self):
        assert normalize_text("  hello  world  ") == "hello world"

    def test_mixed_case(self):
        assert normalize_text("WHAT IS PYTHON?") == "what is python?"

    def test_empty(self):
        assert normalize_text("") == ""

    def test_unicode(self):
        assert normalize_text("Café") == "café"


class TestLanguageDetection:
    def test_english(self):
        assert detect_language("What is the capital of France?") == "en"

    def test_spanish(self):
        assert detect_language("¿Cuál es la capital de Francia?") == "es"

    def test_french(self):
        assert detect_language("Quelle est la capitale de la France?") == "fr"

    def test_german(self):
        assert detect_language("Was ist die Hauptstadt von Frankreich?") == "de"

    def test_empty(self):
        assert detect_language("") == "unknown"

    def test_mixed(self):
        lang = detect_language("Hello world, comment allez-vous?")
        assert lang in ("en", "fr")


class TestContentDetection:
    def test_url_detection(self):
        assert contains_url("Visit https://example.com/page")
        assert contains_url("http://localhost:8000/test")
        assert not contains_url("No URL here")

    def test_email_detection(self):
        assert contains_email("Contact me at test@example.com")
        assert not contains_email("No email here")

    def test_date_detection(self):
        assert contains_date("Event on 2024-01-15")
        assert contains_date("Meeting Jan 15, 2024")
        assert contains_date("Date 01/15/2024")
        assert not contains_date("No date here")

    def test_code_detection(self):
        assert contains_code("def hello():")
        assert contains_code("import numpy as np")
        assert contains_code("print('hello')")
        assert contains_code("var x = 5")
        assert not contains_code("Just a regular question")

    def test_emoji_detection(self):
        assert contains_emoji("How are you 😊")
        assert contains_emoji("I ❤️ Python")
        assert not contains_emoji("Just text")


class TestSyllables:
    def test_simple_words(self):
        assert count_syllables("hello") == 2
        assert count_syllables("world") == 1

    def test_silent_e(self):
        assert count_syllables("make") == 1
        assert count_syllables("like") == 1

    def test_complex(self):
        assert count_syllables("understanding") >= 3


class TestReadability:
    def test_easy_text(self):
        fre = flesch_reading_ease(total_syllables=5, total_words=5, total_sentences=1)
        assert fre > 80

    def test_difficult_text(self):
        fre = flesch_reading_ease(total_syllables=50, total_words=20, total_sentences=1)
        assert fre < 50


class TestTokenization:
    def test_basic(self):
        assert tokenize("hello world") == ["hello", "world"]

    def test_punctuation(self):
        assert tokenize("hello, world!") == ["hello,", "world!"]

    def test_empty(self):
        assert tokenize("") == []

    def test_sentencize(self):
        assert len(sentencize("Hello. World.")) == 2
        assert len(sentencize("Single")) == 1

    def test_is_question(self):
        assert is_question("What is this?")
        assert is_question("How are you?")
        assert not is_question("Hello world")
        assert not is_question("")


class TestSimilarity:
    def test_jaccard_identical(self):
        assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_jaccard_empty(self):
        assert jaccard_similarity(set(), set()) == 0.0

    def test_jaccard_partial(self):
        sim = jaccard_similarity({"a", "b", "c"}, {"a", "b", "d"})
        assert sim == 0.5


class TestQueryAnalyzer:
    def test_basic_analysis(self):
        result = analyzer.analyze("How to learn Python?", "Best way to learn programming")
        assert isinstance(result, QueryAnalysis)
        assert result.original_question_1 == "How to learn Python?"
        assert result.original_question_2 == "Best way to learn programming"
        assert result.metadata_1.word_count > 0
        assert result.metadata_2.word_count > 0
        assert result.processing_time_ms > 0
        assert result.version == "1.0.0"
        assert result.timestamp

    def test_empty_questions(self):
        result = analyzer.analyze("", "")
        assert result.original_question_1 == ""

    def test_similar_questions(self):
        result = analyzer.analyze("What is the capital of France?", "What is the capital of France?")
        assert result.similarity.word_overlap_ratio == 1.0

    def test_different_questions(self):
        result = analyzer.analyze("How to learn Python?", "What is the weather today?")
        assert result.similarity.word_overlap_ratio < 0.5

    def test_serialization(self):
        result = analyzer.analyze("Question 1?", "Question 2?")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["original_question_1"] == "Question 1?"

        j = result.to_json()
        parsed = json.loads(j)
        assert parsed["original_question_1"] == "Question 1?"

        restored = QueryAnalysis.from_dict(d)
        assert restored.original_question_1 == result.original_question_1


class TestPipeline:
    def test_pipeline_run(self):
        result = pipeline.run("Test q1?", "Test q2?")
        assert isinstance(result, QueryAnalysis)

    def test_batch(self):
        pairs = [
            ("Q1?", "Q2?"),
            ("Q3?", "Q4?"),
        ]
        results = pipeline.run_batch(pairs)
        assert len(results) == 2
        assert all(isinstance(r, QueryAnalysis) for r in results)

    def test_dataframe(self):
        results = pipeline.run_batch([("A?", "B?")])
        df = pipeline.to_dataframe(results)
        import pandas

        assert isinstance(df, pandas.DataFrame)


class TestReport:
    def test_report_generation(self):
        result = analyzer.analyze("How to learn Python?", "What is Java?")
        text = report.generate(result)
        assert isinstance(text, str)
        assert len(text) > 100
        assert "QUERY UNDERSTANDING REPORT" in text
        assert "How to learn Python?" in text
        assert "Similarity Features" in text

    def test_short_report(self):
        result = analyzer.analyze("A?", "B?")
        short = report.generate_short(result)
        assert isinstance(short, str)
        assert "Q1:" in short
        assert "Q2:" in short


class TestEdgeCases:
    def test_unicode_and_emoji(self):
        result = analyzer.analyze("What is 🐍 Python? Café au lait?", "¿Cómo se dice Python en español? 😊")
        assert result.metadata_1.contains_emoji or result.metadata_2.contains_emoji
        assert "🐍" in result.original_question_1

    def test_url_with_code(self):
        result = analyzer.analyze("How to fix import error? See https://stackoverflow.com/q/123", "def solve(): pass")
        assert result.metadata_1.contains_urls
        assert result.metadata_2.contains_code

    def test_long_questions(self):
        long_q = " ".join(["word"] * 100) + "?"
        result = analyzer.analyze(long_q, "short?")
        assert result.metadata_1.word_count >= 100
        assert result.metadata_2.word_count < 10

    def test_special_characters(self):
        result = analyzer.analyze("Price is $99.99! (limited offer) >>>", "Normal question?")
        assert result.metadata_1.contains_special_chars
        assert result.metadata_1.symbol_count > 0

    def test_numbers_and_dates(self):
        result = analyzer.analyze("What happened on 2024-01-15?", "The answer is 42")
        assert result.metadata_1.contains_dates
        assert result.metadata_2.contains_numbers

    def test_whitespace(self):
        result = analyzer.analyze("  spaced   out  ", "normal")
        assert result.normalized_question_1 == "spaced out"

    def test_multiple_languages(self):
        result = analyzer.analyze("What is the meaning of life?", "¿Cuál es el sentido de la vida?")
        assert result.metadata_1.language == "en"

    def test_serialization_roundtrip(self):
        original = analyzer.analyze("Test question one?", "Test question two?")
        d = original.to_dict()
        restored = QueryAnalysis.from_dict(d)
        assert restored.original_question_1 == original.original_question_1
        assert restored.original_question_2 == original.original_question_2
        assert restored.metadata_1.word_count == original.metadata_1.word_count
        assert restored.similarity.word_overlap_ratio == original.similarity.word_overlap_ratio
        assert restored.complexity_1.overall == original.complexity_1.overall

    def test_code_snippet_language(self):
        result = analyzer.analyze("How to fix this bug?", "def foo(): pass")
        assert result.metadata_2.contains_code
        self._check_code_features(result)

    def _check_code_features(self, result):
        comp = result.complexity_2
        assert comp.technical > 0


class TestFeatureExtraction:
    def test_token_statistics(self):
        stats = extract_token_statistics("hello world python")
        assert stats.total_tokens == 3
        assert stats.unique_tokens == 3
        assert stats.avg_token_length > 0

    def test_sentence_statistics(self):
        stats = extract_sentence_statistics("Hello. World. Python is great.")
        assert stats.total_sentences == 3
        assert stats.avg_sentence_length_words > 0

    def test_readability_extraction(self):
        read = extract_readability("The cat sat on the mat.")
        assert read.flesch_reading_ease > 0
        assert read.avg_syllables_per_word > 0

    def test_complexity_extraction(self):
        meta = QuestionMetadata(word_count=10, avg_word_length=5.0)
        read = extract_readability("complex words here")
        comp = extract_complexity(meta, read)
        assert comp.overall > 0
        assert comp.lexical >= 0
        assert comp.syntactic >= 0

    def test_similarity_features(self):
        meta_a = extract_question_metadata("hello world")
        meta_b = extract_question_metadata("hello python")
        sim = extract_similarity_features("hello world", "hello python", meta_a, meta_b)
        assert sim.word_overlap_ratio > 0
        assert sim.word_overlap_ratio < 1.0

    def test_identical_similarity(self):
        meta = extract_question_metadata("hello world")
        sim = extract_similarity_features("hello world", "hello world", meta, meta)
        assert sim.word_overlap_ratio == 1.0
        assert sim.char_overlap_ratio == 1.0
