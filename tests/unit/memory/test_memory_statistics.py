from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import (
    MemoryStatistics,
)
from duplicate_question_app._memory.memory_statistics import DefaultMemoryStatistics
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import create_episodic_memory, create_reasoning_memory, create_semantic_memory


class TestMemoryStatistics:
    def test_compute_empty_store(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        result = stats.compute(store)
        assert result.total_entries == 0
        assert result.avg_quality == 0.0
        assert result.avg_confidence == 0.0

    def test_compute_after_store(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        store.store(create_episodic_memory())
        store.store(create_semantic_memory())
        result = stats.compute(store)
        assert result.total_entries == 2

    def test_compute_by_type(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        store.store(create_episodic_memory())
        store.store(create_episodic_memory())
        store.store(create_semantic_memory())
        result = stats.compute(store)
        assert result.total_by_type.get("episodic") == 2
        assert result.total_by_type.get("semantic") == 1

    def test_compute_avg_quality(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(quality_score=0.6)
        e2 = create_episodic_memory(quality_score=1.0)
        store.store(e1)
        store.store(e2)
        result = stats.compute(store)
        assert result.avg_quality == 0.8

    def test_compute_avg_confidence(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        e1 = create_episodic_memory(confidence=0.5)
        e2 = create_episodic_memory(confidence=0.9)
        store.store(e1)
        store.store(e2)
        result = stats.compute(store)
        assert result.avg_confidence == 0.7

    def test_compute_growth_rate(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        for _ in range(10):
            store.store(create_episodic_memory())
        rate = stats.compute_growth_rate(store, hours=24)
        assert rate >= 0.0

    def test_compute_with_deleted_entries(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        e = create_episodic_memory()
        mid = store.store(e)
        store.store(create_semantic_memory())
        store.delete(mid, soft=True)
        result = stats.compute(store)
        assert result.total_entries == 1

    def test_compute_multiple_types(self) -> None:
        stats = DefaultMemoryStatistics()
        store = InMemoryMemoryStore()
        store.store(create_episodic_memory())
        store.store(create_semantic_memory())
        store.store(create_reasoning_memory())
        result = stats.compute(store)
        assert len(result.total_by_type) == 3

    def test_statistics_dataclass(self) -> None:
        s = MemoryStatistics(
            total_entries=10,
            total_by_type={"episodic": 5, "semantic": 5},
            total_size_bytes=5000,
            avg_quality=0.75,
            avg_confidence=0.8,
            oldest_entry=datetime.now() - timedelta(days=10),
            newest_entry=datetime.now(),
            version_count=15,
            deleted_count=2,
        )
        assert s.total_entries == 10
        assert s.avg_quality == 0.75

    def test_statistics_to_dict(self) -> None:
        s = MemoryStatistics(
            total_entries=5,
            total_by_type={"episodic": 5},
            total_size_bytes=2500,
            avg_quality=0.8,
            avg_confidence=0.85,
        )
        d = {
            "total_entries": s.total_entries,
            "total_by_type": s.total_by_type,
            "total_size_bytes": s.total_size_bytes,
            "avg_quality": s.avg_quality,
            "avg_confidence": s.avg_confidence,
        }
        assert d["total_entries"] == 5
