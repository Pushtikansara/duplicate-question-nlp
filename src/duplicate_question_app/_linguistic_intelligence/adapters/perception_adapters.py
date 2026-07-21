"""Adapters that bridge between Phase 1.2 Perception Engine adapters and Phase 1.3 Linguistic Intelligence.

Wraps existing EntityAdapter, NegationAdapter, IntentAdapter, LexicalAdapter
from `_perception.adapters` to reuse previously wrapped linguistic engines.
"""

from __future__ import annotations

from duplicate_question_app._perception.adapters import (
    EntityAdapter,
    IntentAdapter,
    LexicalAdapter,
    LinguisticAdapterFactory,
    NegationAdapter,
)

__all__ = [
    "get_entity_adapter",
    "get_negation_adapter",
    "get_intent_adapter",
    "get_lexical_adapter",
]


def get_entity_adapter() -> EntityAdapter:
    return LinguisticAdapterFactory.create_entity_adapter()


def get_negation_adapter() -> NegationAdapter:
    return LinguisticAdapterFactory.create_negation_adapter()


def get_intent_adapter() -> IntentAdapter:
    return LinguisticAdapterFactory.create_intent_adapter()


def get_lexical_adapter() -> LexicalAdapter:
    return LinguisticAdapterFactory.create_lexical_adapter()
