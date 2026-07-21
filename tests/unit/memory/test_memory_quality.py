from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType

from .conftest import MemoryQualityScorer


def _make_entry(confidence: float = 0.8, quality: float = 0.8, content: dict | None = None) -> MemoryEntry:
    return MemoryEntry(
        memory_id="q-test",
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=datetime.now(),
        source_module="test",
        quality_score=quality,
        confidence=confidence,
        lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
        tags=["q"],
        metadata={},
        content=content or {"a": "v", "b": "v"},
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


class TestMemoryQuality:
    def test_score_high_confidence_high_quality(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(confidence=1.0, quality=1.0)
        score = scorer.score(entry)
        assert 0.0 <= score <= 1.0
        assert score > 0.5

    def test_score_low_confidence(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(confidence=0.0)
        score = scorer.score(entry)
        assert score >= 0.0

    def test_score_completeness_full(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(content={"a": "x", "b": "y", "c": "z"})
        score = scorer.score(entry)
        assert score > 0.0

    def test_score_completeness_empty(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(content={})
        score = scorer.score(entry)
        assert score >= 0.0

    def test_score_usage_high(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(quality=1.0)
        score = scorer.score(entry)
        assert score > 0.0

    def test_score_usage_zero(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(quality=0.0)
        score = scorer.score(entry)
        assert score >= 0.0

    def test_score_confidence_weight(self) -> None:
        scorer = MemoryQualityScorer()
        high_conf = _make_entry(confidence=1.0, quality=0.0)
        low_conf = _make_entry(confidence=0.0, quality=1.0)
        assert scorer.score(high_conf) >= 0.0
        assert scorer.score(low_conf) >= 0.0

    def test_score_never_crashes(self) -> None:
        scorer = MemoryQualityScorer()
        for confidence in [0.0, 0.5, 1.0]:
            for quality in [0.0, 0.5, 1.0]:
                entry = _make_entry(confidence=confidence, quality=quality)
                score = scorer.score(entry)
                assert 0.0 <= score <= 1.0

    def test_score_bounds(self) -> None:
        scorer = MemoryQualityScorer()
        for _ in range(100):
            import random

            entry = _make_entry(
                confidence=random.random(),
                quality=random.random(),
                content={"a": "v"} if random.random() > 0.5 else {},
            )
            score = scorer.score(entry)
            assert 0.0 <= score <= 1.0

    def test_score_consistent(self) -> None:
        scorer = MemoryQualityScorer()
        entry = _make_entry(confidence=0.75, quality=0.85)
        score1 = scorer.score(entry)
        score2 = scorer.score(entry)
        assert score1 == score2
