from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryQuery, MemoryStatus, MemoryType

from .conftest import (
    CompositeRanker,
    ConfidenceRanker,
    QualityRanker,
    RecencyRanker,
)


def _make_entry(mid: str, ts: datetime | None = None, confidence: float = 0.5, quality: float = 0.5) -> MemoryEntry:
    return MemoryEntry(
        memory_id=mid,
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=ts or datetime.now(),
        source_module="test",
        quality_score=quality,
        confidence=confidence,
        lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
        tags=["test"],
        metadata={},
        content={"key": "val"},
        status=MemoryStatus.ACTIVE,
    )


class TestRetrievalRanker:
    def test_recency_ranker_newest_first(self) -> None:
        ranker = RecencyRanker()
        now = datetime.now()
        e1 = _make_entry("old", ts=now - timedelta(hours=10))
        e2 = _make_entry("new", ts=now)
        query = MemoryQuery()
        ranked = ranker.rank([e1, e2], query)
        assert ranked[0].memory_id == "new"
        assert ranked[1].memory_id == "old"

    def test_recency_ranker_oldest_last(self) -> None:
        ranker = RecencyRanker()
        now = datetime.now()
        e1 = _make_entry("old", ts=now - timedelta(days=5))
        e2 = _make_entry("mid", ts=now - timedelta(days=2))
        e3 = _make_entry("new", ts=now)
        ranked = ranker.rank([e3, e1, e2], MemoryQuery())
        assert ranked[0].memory_id == "new"
        assert ranked[2].memory_id == "old"

    def test_confidence_ranker_highest_first(self) -> None:
        ranker = ConfidenceRanker()
        e1 = _make_entry("low", confidence=0.3)
        e2 = _make_entry("high", confidence=0.9)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert ranked[0].memory_id == "high"

    def test_confidence_ranker_tie(self) -> None:
        ranker = ConfidenceRanker()
        e1 = _make_entry("a", confidence=0.8)
        e2 = _make_entry("b", confidence=0.8)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert {r.memory_id for r in ranked} == {"a", "b"}

    def test_quality_ranker_highest_first(self) -> None:
        ranker = QualityRanker()
        e1 = _make_entry("low", quality=0.2)
        e2 = _make_entry("high", quality=0.95)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert ranked[0].memory_id == "high"

    def test_composite_ranker_weights(self) -> None:
        ranker = CompositeRanker()
        e1 = _make_entry("a", confidence=0.9, quality=0.9)
        e2 = _make_entry("b", confidence=0.1, quality=0.1)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert ranked[0].memory_id == "a"

    def test_composite_ranker_default_weights(self) -> None:
        ranker = CompositeRanker()
        assert len(ranker.rankers) == 3

    def test_ranker_empty_list(self) -> None:
        for ranker in [RecencyRanker(), ConfidenceRanker(), QualityRanker(), CompositeRanker()]:
            assert ranker.rank([], MemoryQuery()) == []

    def test_ranker_single_entry(self) -> None:
        e = _make_entry("only")
        for ranker in [RecencyRanker(), ConfidenceRanker(), QualityRanker(), CompositeRanker()]:
            ranked = ranker.rank([e], MemoryQuery())
            assert len(ranked) == 1
            assert ranked[0].memory_id == "only"

    def test_recency_ranker_same_timestamp(self) -> None:
        ranker = RecencyRanker()
        ts = datetime.now()
        e1 = _make_entry("a", ts=ts)
        e2 = _make_entry("b", ts=ts)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert len(ranked) == 2

    def test_quality_ranker_with_identical_scores(self) -> None:
        ranker = QualityRanker()
        e1 = _make_entry("a", quality=0.5)
        e2 = _make_entry("b", quality=0.5)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert {r.memory_id for r in ranked} == {"a", "b"}

    def test_composite_ranker_custom_weights(self) -> None:
        ranker = CompositeRanker(
            rankers=[
                (ConfidenceRanker(), 1.0),
            ]
        )
        e1 = _make_entry("low", confidence=0.3)
        e2 = _make_entry("high", confidence=0.9)
        ranked = ranker.rank([e1, e2], MemoryQuery())
        assert ranked[0].memory_id == "high"

    def test_ranker_does_not_modify_original(self) -> None:
        ranker = RecencyRanker()
        now = datetime.now()
        e1 = _make_entry("a", ts=now - timedelta(hours=1))
        e2 = _make_entry("b", ts=now)
        original = [e1, e2]
        original_ids = [e.memory_id for e in original]
        ranker.rank(original, MemoryQuery())
        assert [e.memory_id for e in original] == original_ids

    def test_multiple_rankers_sequential(self) -> None:
        now = datetime.now()
        e1 = _make_entry("old_high", ts=now - timedelta(hours=5), confidence=0.9)
        e2 = _make_entry("new_low", ts=now, confidence=0.1)
        recency = RecencyRanker()
        confidence = ConfidenceRanker()
        r1 = recency.rank([e1, e2], MemoryQuery())
        assert r1[0].memory_id == "new_low"
        r2 = confidence.rank(r1, MemoryQuery())
        assert r2[0].memory_id == "old_high"

    def test_rank_after_filter(self) -> None:
        ranker = ConfidenceRanker()
        e1 = _make_entry("low", confidence=0.2)
        e2 = _make_entry("high", confidence=0.8)
        filtered = [e for e in [e1, e2] if e.confidence > 0.5]
        ranked = ranker.rank(filtered, MemoryQuery())
        assert len(ranked) == 1
        assert ranked[0].memory_id == "high"
