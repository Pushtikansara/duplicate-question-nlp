from __future__ import annotations

from duplicate_question_app._perception.cognitive_representation import Metadata as PerceptionMetadata
from duplicate_question_app._routing.complexity_estimator import DefaultComplexityEstimator


class TestDefaultComplexityEstimator:
    def setup_method(self):
        self.estimator = DefaultComplexityEstimator()

    def test_empty_questions(self):
        result = self.estimator.estimate("", "")
        assert result.complexity == "uncertain"
        assert result.score == 1.0

    def test_one_empty_question(self):
        result = self.estimator.estimate("Hello", "")
        assert result.complexity == "uncertain"
        assert result.score == 1.0

    def test_greeting_questions(self):
        result = self.estimator.estimate("Hi", "Hello")
        assert result.complexity == "simple"
        assert result.score <= 0.2

    def test_very_short_factual(self):
        result = self.estimator.estimate("What is Python?", "What is AI?")
        assert result.complexity == "simple"
        assert 0.0 <= result.score <= 0.4

    def test_short_definition(self):
        result = self.estimator.estimate("Define NLP", "What is NLP?")
        assert result.complexity == "simple"
        assert result.score <= 0.4

    def test_medium_installation_question(self):
        result = self.estimator.estimate(
            "How to install Python on Ubuntu?",
            "What is the best way to set up Python on Linux?",
        )
        assert result.complexity == "medium"
        assert 0.4 <= result.score <= 0.7

    def test_medium_comparison_keywords(self):
        result = self.estimator.estimate(
            "Python vs Java performance",
            "Compare Python and Java speed",
        )
        assert result.complexity in ("medium", "complex")

    def test_medium_configure_keywords(self):
        result = self.estimator.estimate(
            "How to configure Django settings?",
            "Setup Django configuration tutorial",
        )
        assert result.complexity == "medium"

    def test_complex_long_multi_sentence(self):
        result = self.estimator.estimate(
            "What is the difference between Python 2 and Python 3? "
            "How does the migration affect existing codebases? "
            "What are best practices for transitioning?",
            "Compare Python versions and discuss migration strategies for enterprise applications with legacy code.",
        )
        assert result.complexity == "complex"
        assert result.score >= 0.6

    def test_complex_with_entities(self):
        result = self.estimator.estimate(
            "How does TensorFlow 2.0 compare to PyTorch for NLP?",
            "What are the differences between TensorFlow and PyTorch?",
        )
        assert result.complexity in ("medium", "complex")

    def test_uncertain_with_ambiguity(self):
        result = self.estimator.estimate(
            "Maybe Python is better than Java? Perhaps not sure.",
            "Probably Python might be the best choice?",
        )
        assert result.complexity in ("complex", "uncertain")
        assert result.score >= 0.5

    def test_complex_with_code_snippets(self):
        result = self.estimator.estimate(
            "What does this code do: `def foo(): return 42`",
            "Explain this: `import os; os.path.join('a', 'b')`",
        )
        assert result.complexity in ("medium", "complex")
        assert result.score >= 0.3

    def test_complex_with_urls(self):
        result = self.estimator.estimate(
            "Check https://example.com for details",
            "See docs at http://docs.python.org",
        )
        assert result.score > 0

    def test_all_features_populated(self):
        result = self.estimator.estimate("What is Python?", "What is AI?")
        assert "avg_word_count" in result.features
        assert "avg_char_len" in result.features
        assert "word_count_a" in result.features
        assert "word_count_b" in result.features
        assert "ambiguity_count" in result.features
        assert "complex_keyword_count" in result.features
        assert "medium_keyword_count" in result.features
        assert "simple_word_count" in result.features
        assert "has_multi_sentence" in result.features
        assert "has_code" in result.features
        assert "has_url" in result.features
        assert "entity_count" in result.features

    def test_score_bounds_low(self):
        result = self.estimator.estimate("Hi", "Hello")
        assert 0.0 <= result.score <= 1.0

    def test_score_bounds_high(self):
        result = self.estimator.estimate(
            "Maybe perhaps possibly this is unclear and uncertain? "
            "Could it be that we need to think about the implications "
            "and analyze the impact of this decision on the architecture? "
            "Let me compare and contrast the underlying mechanisms.",
            "I'm not sure about the relationship between these concepts. "
            "The impact might be significant. Perhaps we should evaluate.",
        )
        assert 0.0 <= result.score <= 1.0

    def test_explanation_not_empty(self):
        result = self.estimator.estimate("What is Python?", "What is AI?")
        assert len(result.explanation) > 0

    def test_different_lengths(self):
        result = self.estimator.estimate("Hi", "What is the detailed explanation of quantum computing?")
        assert result.features["avg_word_count"] >= 4

    def test_complex_keywords_score(self):
        result = self.estimator.estimate(
            "Analyze the impact of this change",
            "Evaluate the effect of the new architecture",
        )
        assert result.complexity in ("medium", "complex")

    def test_with_perception_metadata(self):
        metadata = PerceptionMetadata(
            length=50,
            char_count=50,
            word_count=8,
            sentence_count=1,
            question_type="wh-what",
        )
        result = self.estimator.estimate("What is Python?", "What is AI?", metadata=metadata)
        assert result.features["question_type_a"] == "wh-what"

    def test_entity_count_from_metadata(self):
        metadata = PerceptionMetadata(
            length=200,
            char_count=200,
            word_count=30,
            sentence_count=3,
            question_type="wh-how",
        )
        result = self.estimator.estimate(
            "Complex question with many entities",
            "Another complex question",
            metadata=metadata,
        )
        assert "entity_count" in result.features

    def test_exception_handling(self):
        result = self.estimator.estimate(None, None)  # type: ignore[arg-type]
        assert result.complexity == "uncertain"
        assert result.score == 1.0

    def test_score_monotonic(self):
        simple = self.estimator.estimate("Hi", "Hello")
        medium = self.estimator.estimate(
            "How to install Python?",
            "Setup Python configuration",
        )
        complex_r = self.estimator.estimate(
            "Analyze the impact of this change on the architecture "
            "and evaluate the implications for the system design.",
            "Compare and contrast the underlying mechanisms and their effect on performance.",
        )
        assert simple.score <= medium.score <= complex_r.score
