"""Tests for the Text Normalizer."""

from __future__ import annotations

import pytest

from duplicate_question_app._perception.config import NormalizerConfig
from duplicate_question_app._perception.exceptions import NormalizationError
from duplicate_question_app._perception.normalizer import DefaultTextNormalizer, NoOpTextNormalizer


class TestDefaultTextNormalizer:
    def test_normalize_basic_text(self):
        normalizer = DefaultTextNormalizer()
        result, report = normalizer.normalize("  Hello World!  ")
        assert result == "hello world!"
        assert report.valid

    def test_normalize_with_abbreviation(self):
        normalizer = DefaultTextNormalizer(NormalizerConfig(expand_abbreviations=True))
        result, _ = normalizer.normalize("What is AI?")
        assert "artificial intelligence" in result

    def test_normalize_with_typo(self):
        normalizer = DefaultTextNormalizer(NormalizerConfig(fix_typos=True))
        result, _ = normalizer.normalize("What is artifical intelligence?")
        assert "artificial" in result

    def test_normalize_empty_string(self):
        normalizer = DefaultTextNormalizer()
        result, report = normalizer.normalize("")
        assert result == ""
        assert not report.valid

    def test_normalize_whitespace_only(self):
        normalizer = DefaultTextNormalizer()
        result, report = normalizer.normalize("   ")
        assert result == ""
        assert not report.valid

    def test_normalize_punctuation(self):
        normalizer = DefaultTextNormalizer()
        result, _ = normalizer.normalize("Hello!!! How are you??")
        assert "hello! how are you?" in result

    def test_normalize_case(self):
        normalizer = DefaultTextNormalizer(NormalizerConfig(lowercase=True))
        result, _ = normalizer.normalize("UPPERCASE Text")
        assert result == "uppercase text"

    def test_normalize_html_stripping(self):
        normalizer = DefaultTextNormalizer()
        result, _ = normalizer.normalize("<p>Hello</p>")
        assert result.strip() == "hello"

    def test_normalize_url_stripping(self):
        normalizer = DefaultTextNormalizer()
        result, _ = normalizer.normalize("Check https://example.com")
        assert "[url]" in result

    def test_normalize_no_expand_no_fix(self):
        normalizer = DefaultTextNormalizer(NormalizerConfig(expand_abbreviations=False, fix_typos=False))
        result, _ = normalizer.normalize("What is artifical AI?")
        assert "artifical" in result
        assert "ai" in result

    def test_normalize_non_string_raises(self):
        normalizer = DefaultTextNormalizer()
        with pytest.raises(NormalizationError):
            normalizer.normalize(123)  # type: ignore[arg-type]


class TestNoOpTextNormalizer:
    def test_noop_passthrough(self):
        normalizer = NoOpTextNormalizer()
        result, report = normalizer.normalize("  Hello World!  ")
        assert result == "Hello World!"
        assert report.valid
