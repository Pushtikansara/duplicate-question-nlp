"""Tests for the Tokenizer Wrapper."""

from __future__ import annotations

import pytest

from duplicate_question_app._perception.config import TokenizerConfig
from duplicate_question_app._perception.tokenizer_wrapper import TokenizerFactory, WhitespaceTokenizer


class TestWhitespaceTokenizer:
    def test_tokenize_basic(self):
        tokenizer = WhitespaceTokenizer()
        tokens = tokenizer.tokenize("hello world")
        assert len(tokens) == 2
        assert tokens[0].text == "hello"
        assert tokens[1].text == "world"

    def test_tokenize_empty(self):
        tokenizer = WhitespaceTokenizer()
        tokens = tokenizer.tokenize("")
        assert tokens == []

    def test_tokenize_with_punctuation(self):
        tokenizer = WhitespaceTokenizer()
        tokens = tokenizer.tokenize("hello, world!")
        assert len(tokens) >= 2
        assert tokens[0].text == "hello"

    def test_tokenize_lowercase(self):
        tokenizer = WhitespaceTokenizer(TokenizerConfig(lowercase=True))
        tokens = tokenizer.tokenize("Hello World")
        assert tokens[0].text == "hello"

    def test_tokenize_truncation(self):
        tokenizer = WhitespaceTokenizer(TokenizerConfig(max_length=2, truncation=True))
        tokens = tokenizer.tokenize("a b c d e")
        assert len(tokens) == 2
        assert tokens[0].text == "a"
        assert tokens[1].text == "b"

    def test_tokenize_positions(self):
        tokenizer = WhitespaceTokenizer()
        tokens = tokenizer.tokenize("hello world")
        assert tokens[0].start == 0
        assert tokens[0].end == 5
        assert tokens[1].start == 6
        assert tokens[1].end == 11


class TestTokenizerFactory:
    def test_create_whitespace(self):
        tokenizer = TokenizerFactory.create(TokenizerConfig(strategy="whitespace"))
        assert isinstance(tokenizer, WhitespaceTokenizer)

    def test_create_unknown_raises(self):
        from duplicate_question_app._perception.exceptions import TokenizationError

        try:
            TokenizerFactory.create(TokenizerConfig(strategy="unknown"))
            pytest.fail("Should have raised")
        except TokenizationError:
            pass
