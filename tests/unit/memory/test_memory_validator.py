from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_validator import DefaultMemoryValidator


def _make_entry(**overrides: object) -> MemoryEntry:
    base: dict = {
        "memory_id": "test-id",
        "memory_type": MemoryType.EPISODIC,
        "version": 1,
        "timestamp": datetime.now(),
        "source_module": "test",
        "quality_score": 0.8,
        "confidence": 0.8,
        "lineage": MemoryLineage(created_by="test", created_at=datetime.now()),
        "tags": ["valid"],
        "metadata": {},
        "content": {
            "question_a": "Q1",
            "question_b": "Q2",
            "pipeline_used": "p",
            "decision": "d",
        },
        "embedding": None,
        "expires_at": None,
        "status": MemoryStatus.ACTIVE,
    }
    base.update(overrides)
    return MemoryEntry(**base)


class TestMemoryValidator:
    def test_validate_valid_entry(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry()
        valid, errors = validator.validate(entry)
        assert valid is True
        assert errors == []

    def test_validate_empty_id(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(memory_id="")
        valid, errors = validator.validate(entry)
        assert valid is False
        assert any("memory_id" in e for e in errors)

    def test_validate_negative_confidence(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(confidence=-0.1)
        valid, errors = validator.validate(entry)
        assert valid is False
        assert any("confidence" in e for e in errors)

    def test_validate_over_confidence(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(confidence=1.5)
        valid, errors = validator.validate(entry)
        assert valid is False
        assert any("confidence" in e for e in errors)

    def test_validate_negative_quality(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(quality_score=-0.5)
        valid, errors = validator.validate(entry)
        assert valid is False
        assert any("quality" in e or "quality_score" in e for e in errors)

    def test_validate_batch(self) -> None:
        validator = DefaultMemoryValidator()
        entries = [
            _make_entry(memory_id="valid-1"),
            _make_entry(memory_id="valid-2"),
        ]
        results = validator.validate_batch(entries)
        assert len(results) == 2
        assert all(r[0] is True for r in results)

    def test_validate_batch_mixed(self) -> None:
        validator = DefaultMemoryValidator()
        entries = [
            _make_entry(memory_id="good"),
            _make_entry(memory_id="", confidence=-1.0, quality_score=-0.5),
        ]
        results = validator.validate_batch(entries)
        assert results[0][0] is True
        assert results[1][0] is False

    def test_validate_version_zero(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(version=0)
        valid, errors = validator.validate(entry)
        assert valid is False
        assert any("version" in e for e in errors)

    def test_validate_missing_content(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(content={})
        valid, errors = validator.validate(entry)
        assert valid is False

    def test_validate_none_fields(self) -> None:
        validator = DefaultMemoryValidator()
        entry = _make_entry(memory_id=None)  # type: ignore[arg-type]
        valid, errors = validator.validate(entry)
        assert valid is False
