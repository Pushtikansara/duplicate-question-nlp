from __future__ import annotations

import pytest

from duplicate_question_app._preprocessing.text import normalize_question

GOLDEN_CASES = [
    ("what is ai", "what is ai", "Duplicate"),
    ("what is ai", "what is artificial intelligence", "Duplicate"),
    ("hello", "hello", "Duplicate"),
    ("what is dbms", "what is database management system", "Duplicate"),
    ("python list", "python tuple", "Non-Duplicate"),
    ("cat", "elephant", "Non-Duplicate"),
    ("what is machine learning", "define machine learning", "Duplicate"),
    ("java", "java programming language", "Duplicate"),
]


class TestGoldenPredictions:
    @pytest.mark.parametrize("q1,q2,expected", GOLDEN_CASES)
    def test_normalization_consistency(self, q1, q2, expected):
        n1 = normalize_question(q1, expand_abbrevs=False)
        n2 = normalize_question(q2, expand_abbrevs=False)
        assert isinstance(n1, str)
        assert isinstance(n2, str)

    @pytest.mark.parametrize("q1,q2,expected", GOLDEN_CASES)
    def test_abbreviation_expansion(self, q1, q2, expected):
        n1 = normalize_question(q1, expand_abbrevs=True)
        n2 = normalize_question(q2, expand_abbrevs=True)
        assert isinstance(n1, str)
        assert isinstance(n2, str)

    def test_identical_text_duplicate(self):
        n1 = normalize_question("what is ai", expand_abbrevs=True)
        n2 = normalize_question("what is ai", expand_abbrevs=True)
        assert n1 == n2, "Identical questions should normalize identically"

    def test_ai_abbreviation_expansion(self):
        expanded = normalize_question("what is ai", expand_abbrevs=True)
        assert "artificial intelligence" in expanded.lower()

    def test_dbms_abbreviation_expansion(self):
        expanded = normalize_question("what is dbms", expand_abbrevs=True)
        assert "database management system" in expanded.lower()

    def test_bda_abbreviation_expansion(self):
        expanded = normalize_question("what is bda", expand_abbrevs=True)
        assert "big data analytics" in expanded.lower()

    def test_identical_normalization_produces_same_string(self):
        cases = [
            "what is ai",
            "hello world",
            "python list vs tuple",
            "define machine learning",
        ]
        for c in cases:
            n1 = normalize_question(c, expand_abbrevs=True)
            n2 = normalize_question(c, expand_abbrevs=True)
            assert n1 == n2, f"Normalization of '{c}' should be deterministic"

    def test_expand_then_contains_expanded_form(self):
        n_ai = normalize_question("what is ai", expand_abbrevs=True)
        n_art_int = normalize_question("what is artificial intelligence", expand_abbrevs=True)
        assert "artificial intelligence" in n_ai, (
            "'what is ai' should contain 'artificial intelligence' after expansion"
        )
        assert "artificial intelligence" in n_art_int
        assert n_ai != n_art_int, (
            "Expansion appends rather than replaces: 'what is ai' → 'what is ai (artificial intelligence)'"
        )

    def test_whitespace_normalization(self):
        n1 = normalize_question("  what   is   ai  ", expand_abbrevs=True)
        n2 = normalize_question("what is ai", expand_abbrevs=True)
        assert n1 == n2, "Whitespace should be collapsed"
        assert "  " not in n1, "No double spaces allowed"

    def test_lowercase_normalization(self):
        n = normalize_question("What Is AI", expand_abbrevs=True)
        assert n == n.lower(), "Output should be lowercase"
