"""Tests for CognitiveRepresentation data model."""

from __future__ import annotations

from duplicate_question_app._perception.cognitive_representation import (
    CognitiveRepresentation,
    Entity,
    LinguisticFeatures,
    Metadata,
    Sentence,
    Token,
    ValidationReport,
)


class TestCognitiveRepresentation:
    def test_create_basic_representation(self):
        rep = CognitiveRepresentation(
            raw_text="How to install Python?",
            normalized_text="how to install python?",
            language="en",
            language_confidence=0.95,
            tokens=[],
            sentences=[],
            linguistic=LinguisticFeatures(),
            metadata=Metadata(),
            validation=ValidationReport(),
        )
        assert rep.raw_text == "How to install Python?"
        assert rep.normalized_text == "how to install python?"
        assert rep.language == "en"
        assert rep.pipeline_version == "1.2.0"

    def test_to_dict(self):
        rep = CognitiveRepresentation(
            raw_text="Hello world",
            normalized_text="hello world",
            language="en",
            language_confidence=0.9,
            tokens=[Token(text="hello", start=0, end=5), Token(text="world", start=6, end=11)],
            sentences=[Sentence(text="Hello world", start=0, end=11)],
            linguistic=LinguisticFeatures(
                entities=[Entity(entity_type="test", value="world", start=6, end=11)],
                intent="greeting",
                intent_confidence=0.8,
            ),
            metadata=Metadata(word_count=2, char_count=11, sentence_count=1),
            validation=ValidationReport(valid=True),
            processing_time_ms=1.5,
        )
        d = rep.to_dict()
        assert d["raw_text"] == "Hello world"
        assert d["language"] == "en"
        assert len(d["tokens"]) == 2
        assert len(d["sentences"]) == 1
        assert len(d["linguistic"]["entities"]) == 1
        assert d["linguistic"]["intent"] == "greeting"
        assert d["metadata"]["word_count"] == 2
        assert d["processing_time_ms"] == 1.5

    def test_empty_representation(self):
        rep = CognitiveRepresentation(
            raw_text="",
            normalized_text="",
            language="",
            language_confidence=0.0,
            tokens=[],
            sentences=[],
            linguistic=LinguisticFeatures(),
            metadata=Metadata(),
            validation=ValidationReport(),
        )
        assert rep.raw_text == ""
        assert len(rep.tokens) == 0

    def test_representation_with_extra(self):
        rep = CognitiveRepresentation(
            raw_text="test",
            normalized_text="test",
            language="en",
            language_confidence=1.0,
            tokens=[],
            sentences=[],
            linguistic=LinguisticFeatures(),
            metadata=Metadata(),
            validation=ValidationReport(),
            extra={"source": "test_suite", "id": 42},
        )
        assert rep.extra["source"] == "test_suite"
        assert rep.extra["id"] == 42
