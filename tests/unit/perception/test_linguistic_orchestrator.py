"""Tests for the Linguistic Analyzer Orchestrator."""

from __future__ import annotations

from duplicate_question_app._perception.adapters import (
    DefaultEntityAdapter,
    DefaultIntentAdapter,
    DefaultNegationAdapter,
)
from duplicate_question_app._perception.linguistic_orchestrator import DefaultLinguisticOrchestrator


class TestDefaultLinguisticOrchestrator:
    def test_analyze_empty_text(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("")
        assert len(features.entities) == 0
        assert len(features.negations) == 0
        assert features.intent is None

    def test_analyze_whitespace_only(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("   ")
        assert len(features.entities) == 0

    def test_analyze_with_entities(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("How do I install Python on Ubuntu?")
        entity_types = {e.entity_type for e in features.entities}
        assert "programming_language" in entity_types

    def test_analyze_with_intent(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("What is the best way to learn Python?")
        assert features.intent is not None

    def test_analyze_with_negation(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("How do I disable notifications?")
        assert len(features.negations) > 0

    def test_analyze_lexical_density(self):
        orchestrator = DefaultLinguisticOrchestrator()
        features = orchestrator.analyze("How to install Python on Ubuntu?")
        assert features.lexical_density >= 0.0

    def test_entity_adapter(self):
        adapter = DefaultEntityAdapter()
        entities = adapter.extract("Install Python and Docker on Ubuntu")
        types = {e.entity_type for e in entities}
        assert "programming_language" in types

    def test_negation_adapter(self):
        adapter = DefaultNegationAdapter()
        negations = adapter.detect("How to disable notifications?")
        assert len(negations) > 0

    def test_intent_adapter(self):
        adapter = DefaultIntentAdapter()
        intent, confidence = adapter.detect("What is machine learning?")
        assert intent == "definition"
        assert confidence > 0.0
