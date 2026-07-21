"""Tests for Linguistic Intelligence adapters."""

from __future__ import annotations

from duplicate_question_app._linguistic_intelligence.adapters.perception_adapters import (
    get_entity_adapter,
    get_intent_adapter,
    get_lexical_adapter,
    get_negation_adapter,
)


class TestAdapters:
    def test_entity_adapter(self):
        adapter = get_entity_adapter()
        entities = adapter.extract("How to install Python on Ubuntu?")
        types = {e.entity_type for e in entities}
        assert "programming_language" in types

    def test_negation_adapter(self):
        adapter = get_negation_adapter()
        negations = adapter.detect("How to disable notifications?")
        assert len(negations) > 0

    def test_intent_adapter(self):
        adapter = get_intent_adapter()
        intent, conf = adapter.detect("What is machine learning?")
        assert intent == "definition"
        assert conf > 0.0

    def test_lexical_adapter(self):
        adapter = get_lexical_adapter()
        result = adapter.analyze("How to install Python?")
        assert "nouns" in result or "lexical_density" in result
