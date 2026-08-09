from __future__ import annotations

import pytest

from ares.orchestration import (
    CACHE_SCHEMA_VERSION,
    build_query_understanding_cache_key,
    normalize_cache_text,
)
from ares.orchestration.cache_key import DEFAULT_ANALYZER_VERSION


class TestNormalizeCacheText:
    def test_empty(self):
        assert normalize_cache_text("") == ""

    def test_whitespace_strip_and_collapse(self):
        assert normalize_cache_text("  what   is  python  ") == "what is python"

    def test_case_insensitive(self):
        assert normalize_cache_text("What Is PYTHON?") == "what is python?"

    def test_unicode_nfkc_compatibility(self):
        assert normalize_cache_text("ｆｕｌｌｗｉｄｔｈ") == "fullwidth"

    def test_unicode_combining(self):
        assert normalize_cache_text("caf\u00e9") == normalize_cache_text("cafe\u0301")

    def test_punctuation_preserved(self):
        assert normalize_cache_text("Hello!") != normalize_cache_text("Hello")

    def test_punctuation_spacing_preserved(self):
        assert normalize_cache_text("python ?") != normalize_cache_text("python?")

    def test_non_string(self):
        with pytest.raises((TypeError, AttributeError)):
            normalize_cache_text(None)  # type: ignore[arg-type]


class TestQueryUnderstandingCacheKey:
    def test_same_input_same_key(self):
        key1 = build_query_understanding_cache_key("What is Python?", "What is python?")
        key2 = build_query_understanding_cache_key("What is Python?", "What is python?")
        assert key1 == key2

    def test_deterministic_across_calls(self):
        key1 = build_query_understanding_cache_key("How do I sort a list in Python?", "How to sort lists?")
        key2 = build_query_understanding_cache_key("How do I sort a list in Python?", "How to sort lists?")
        assert key1 == key2

    def test_whitespace_normalization(self):
        key1 = build_query_understanding_cache_key("What is  Python?", "  what is python  ")
        key2 = build_query_understanding_cache_key("What is Python?", "what is python")
        assert key1 == key2

    def test_case_insensitive(self):
        key1 = build_query_understanding_cache_key("WHAT IS PYTHON?", "What is Python?")
        key2 = build_query_understanding_cache_key("what is python?", "what is python?")
        assert key1 == key2

    def test_unicode(self):
        key1 = build_query_understanding_cache_key("caf\u00e9 vs cafe", "What is a caf\u00e9?")
        key2 = build_query_understanding_cache_key("cafe\u0301 vs cafe", "What is a cafe\u0301?")
        assert key1 == key2

    def test_punctuation_affects_key(self):
        key1 = build_query_understanding_cache_key("Hello!", "Hello?")
        key2 = build_query_understanding_cache_key("Hello", "Hello")
        assert key1 != key2

    def test_reversed_questions_different_key(self):
        key1 = build_query_understanding_cache_key("What is Python?", "What is C++?")
        key2 = build_query_understanding_cache_key("What is C++?", "What is Python?")
        assert key1 != key2

    def test_schema_version_change_invalidates(self):
        key1 = build_query_understanding_cache_key("What is Python?", "What is python?", schema_version="1")
        key2 = build_query_understanding_cache_key("What is Python?", "What is python?", schema_version="2")
        assert key1 != key2

    def test_analyzer_version_change_invalidates(self):
        key1 = build_query_understanding_cache_key("What is Python?", "What is python?", analyzer_version="1.0.0")
        key2 = build_query_understanding_cache_key("What is Python?", "What is python?", analyzer_version="1.1.0")
        assert key1 != key2

    def test_analyzer_version_default_resolves(self):
        key = build_query_understanding_cache_key("What is Python?", "What is python?")
        explicit = build_query_understanding_cache_key(
            "What is Python?", "What is python?", analyzer_version=DEFAULT_ANALYZER_VERSION
        )
        assert key == explicit

    def test_schema_version_default_constant(self):
        key = build_query_understanding_cache_key("a", "b")
        explicit = build_query_understanding_cache_key("a", "b", schema_version=CACHE_SCHEMA_VERSION)
        assert key == explicit

    def test_empty_input(self):
        key = build_query_understanding_cache_key("", "")
        assert len(key) == 64
        assert build_query_understanding_cache_key("", "") == key

    def test_long_input(self):
        long_text = "word " * 20000
        key = build_query_understanding_cache_key(long_text, "short question?")
        assert len(key) == 64

    def test_key_is_sha256_hex(self):
        key = build_query_understanding_cache_key("What is Python?", "What is python?")
        assert len(key) == 64
        int(key, 16)

    def test_key_does_not_leak_raw_text(self):
        key = build_query_understanding_cache_key("What is Python?", "What is python?")
        assert "python" not in key
        assert "What" not in key
