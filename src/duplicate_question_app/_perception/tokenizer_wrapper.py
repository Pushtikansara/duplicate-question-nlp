"""Tokenizer Wrapper — third stage of the Cognitive Perception Pipeline.

Provides multiple tokenization strategies with a unified interface.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import cast

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.cognitive_representation import Token
from duplicate_question_app._perception.config import TokenizerConfig
from duplicate_question_app._perception.exceptions import TokenizationError

log = get_logger(__name__)

_WORD_PATTERN = re.compile(r"\b\w+(?:[-']\w+)*\b")


class Tokenizer(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[Token]: ...


class WhitespaceTokenizer(Tokenizer):
    def __init__(self, config: TokenizerConfig | None = None):
        self._config = config or TokenizerConfig()
        self._logger = get_logger(f"{__name__}.WhitespaceTokenizer")

    def tokenize(self, text: str) -> list[Token]:
        if not text:
            return []
        tokens: list[Token] = []
        for match in _WORD_PATTERN.finditer(text):
            token_text = match.group()
            if self._config.lowercase:
                token_text = token_text.lower()
            token = Token(text=token_text, start=match.start(), end=match.end())
            tokens.append(token)
        if self._config.truncation and len(tokens) > self._config.max_length:
            tokens = tokens[: self._config.max_length]
        return tokens


class RegexTokenizer(Tokenizer):
    def __init__(self, config: TokenizerConfig | None = None, pattern: re.Pattern | None = None):
        self._config = config or TokenizerConfig()
        self._pattern = pattern or re.compile(r"\w+|[^\w\s]")
        self._logger = get_logger(f"{__name__}.RegexTokenizer")

    def tokenize(self, text: str) -> list[Token]:
        if not text:
            return []
        tokens: list[Token] = []
        for match in self._pattern.finditer(text):
            token_text = match.group()
            if self._config.lowercase:
                token_text = token_text.lower()
            token = Token(text=token_text, start=match.start(), end=match.end())
            tokens.append(token)
        if self._config.truncation and len(tokens) > self._config.max_length:
            tokens = tokens[: self._config.max_length]
        return tokens


class TokenizerFactory:
    _strategies: dict[str, type] = {
        "whitespace": WhitespaceTokenizer,
        "regex": RegexTokenizer,
    }

    @classmethod
    def create(cls, config: TokenizerConfig) -> Tokenizer:
        strategy = config.strategy
        if strategy not in cls._strategies:
            raise TokenizationError(
                f"Unknown tokenizer strategy: {strategy}",
                context="TokenizerFactory.create",
                resolution=f"Choose from: {list(cls._strategies.keys())}",
            )
        return cast(Tokenizer, cls._strategies[strategy](config))

    @classmethod
    def register(cls, name: str, tokenizer_cls: type[Tokenizer]) -> None:
        cls._strategies[name] = tokenizer_cls
