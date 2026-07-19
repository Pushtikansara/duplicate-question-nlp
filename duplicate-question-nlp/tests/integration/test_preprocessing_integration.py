from __future__ import annotations

import pytest

from duplicate_question_app._preprocessing.text import normalize_question


class TestPreprocessingIntegration:
    @pytest.mark.integration
    def test_preprocessing_real_world_examples(self):
        examples = [
            ("How to learn Python programming in 2024?", "how to learn python programming in 2024?"),
            ("What's the best way to learn machine learning?", "what's the best way to learn machine learning?"),
            ("I can't find my keys!! Where are they?", "i can't find my keys! where are they?"),
            ("Visit us at https://example.com for more info", "visit us at [url] for more info"),
            ("Contact: john.doe@email.com for support", "contact: [url] for support"),
        ]
        for raw, expected in examples:
            result = normalize_question(raw)
            assert expected in result.lower(), f"Expected '{expected}' in '{result}'"

    @pytest.mark.integration
    def test_preprocessing_extreme_lengths(self):
        short = normalize_question("Hi")
        assert isinstance(short, str)
        long_text = "word " * 5000
        long_result = normalize_question(long_text)
        assert isinstance(long_result, str)

    @pytest.mark.integration
    def test_preprocessing_preserves_semantic_content(self):
        tests = [
            ("How to learn Python?", "learn"),
            ("What is the capital of France?", "france"),
            ("Best practices for coding", "coding"),
        ]
        for text, keyword in tests:
            result = normalize_question(text)
            assert keyword in result.lower(), f"Keyword '{keyword}' lost in '{result}'"

    @pytest.mark.integration
    def test_preprocessing_idempotent(self):
        texts = [
            "How to learn Python?",
            "What's happening?",
            "I can't believe it!",
            "Hello, World!!!",
        ]
        for t in texts:
            r1 = normalize_question(t)
            r2 = normalize_question(r1)
            assert r1 == r2, f"Not idempotent: '{r1}' -> '{r2}'"
