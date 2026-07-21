"""Tests for the Validator."""

from __future__ import annotations

import pytest

from duplicate_question_app._perception.cognitive_representation import (
    CognitiveRepresentation,
    LinguisticFeatures,
    Metadata,
    ValidationReport,
)
from duplicate_question_app._perception.exceptions import ValidationError
from duplicate_question_app._perception.validator import DefaultValidator


class TestDefaultValidator:
    def test_validate_valid_text(self):
        validator = DefaultValidator()
        report = validator.validate_text("Hello world")
        assert report.valid
        assert len(report.errors) == 0

    def test_validate_empty_text(self):
        validator = DefaultValidator()
        with pytest.raises(ValidationError):
            validator.validate_text("")

    def test_validate_whitespace_only(self):
        validator = DefaultValidator()
        with pytest.raises(ValidationError):
            validator.validate_text("   ")

    def test_validate_representation_valid(self):
        validator = DefaultValidator()
        rep = CognitiveRepresentation(
            raw_text="hello",
            normalized_text="hello",
            language="en",
            language_confidence=0.9,
            tokens=[],
            sentences=[],
            linguistic=LinguisticFeatures(),
            metadata=Metadata(),
            validation=ValidationReport(),
        )
        report = validator.validate_representation(rep)
        assert report.valid

    def test_validate_representation_empty_raw(self):
        validator = DefaultValidator()
        rep = CognitiveRepresentation(
            raw_text="",
            normalized_text="",
            language="en",
            language_confidence=0.0,
            tokens=[],
            sentences=[],
            linguistic=LinguisticFeatures(),
            metadata=Metadata(),
            validation=ValidationReport(),
        )
        report = validator.validate_representation(rep)
        assert not report.valid
        assert any("empty" in e.lower() for e in report.errors)
