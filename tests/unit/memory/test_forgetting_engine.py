from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import (
    AgingPolicy,
    DefaultForgettingEngine,
)


def _make_entry(mid: str, ts: datetime | None = None, quality: float = 0.8, confidence: float = 0.8) -> MemoryEntry:
    return MemoryEntry(
        memory_id=mid,
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=ts or datetime.now(),
        source_module="test",
        quality_score=quality,
        confidence=confidence,
        lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
        tags=["f"],
        metadata={},
        content={"k": "v"},
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


class TestForgettingEngine:
    def test_apply_policies_no_entries(self) -> None:
        engine = DefaultForgettingEngine()
        store = InMemoryMemoryStore()
        affected = engine.apply_policies(store)
        assert affected == []

    def test_apply_age_policy_old_entries(self) -> None:
        engine = DefaultForgettingEngine(aging_policy=AgingPolicy(threshold_days=1))
        store = InMemoryMemoryStore()
        old = _make_entry("old", ts=datetime.now() - timedelta(days=10))
        store.store(old)
        affected = engine.apply_policies(store)
        assert "old" in affected

    def test_apply_age_policy_recent_entries(self) -> None:
        engine = DefaultForgettingEngine(aging_policy=AgingPolicy(threshold_days=90))
        store = InMemoryMemoryStore()
        recent = _make_entry("recent", ts=datetime.now())
        store.store(recent)
        affected = engine.apply_policies(store)
        assert "recent" not in affected

    def test_apply_quality_policy_low_quality(self) -> None:
        engine = DefaultForgettingEngine(quality_threshold=0.5)
        store = InMemoryMemoryStore()
        low = _make_entry("low-quality", quality=0.1)
        store.store(low)
        affected = engine.apply_policies(store)
        assert "low-quality" in affected

    def test_apply_quality_policy_high_quality(self) -> None:
        engine = DefaultForgettingEngine(quality_threshold=0.5)
        store = InMemoryMemoryStore()
        high = _make_entry("high-quality", quality=0.9)
        store.store(high)
        affected = engine.apply_policies(store)
        assert "high-quality" not in affected

    def test_apply_duplicate_policy(self) -> None:
        engine = DefaultForgettingEngine()
        store = InMemoryMemoryStore()
        e = _make_entry("unique")
        store.store(e)
        affected = engine.apply_policies(store)
        assert isinstance(affected, list)

    def test_calculate_age_score_recent(self) -> None:
        engine = DefaultForgettingEngine()
        recent = _make_entry("recent", ts=datetime.now())
        score = engine.calculate_age_score(recent)
        assert 0.0 <= score <= 1.0
        assert score < 0.1

    def test_calculate_age_score_old(self) -> None:
        engine = DefaultForgettingEngine(aging_policy=AgingPolicy(threshold_days=1))
        old = _make_entry("old", ts=datetime.now() - timedelta(days=5))
        score = engine.calculate_age_score(old)
        assert score > 0.5

    def test_aging_policy_should_archive(self) -> None:
        policy = AgingPolicy(threshold_days=1)
        old = _make_entry("old", ts=datetime.now() - timedelta(days=10))
        assert policy.should_archive(old) is True

    def test_aging_policy_should_not_archive(self) -> None:
        policy = AgingPolicy(threshold_days=90)
        recent = _make_entry("recent", ts=datetime.now())
        assert policy.should_archive(recent) is False

    def test_aging_policy_age_score(self) -> None:
        policy = AgingPolicy(threshold_days=1)
        now = datetime.now()
        e = _make_entry("test", ts=now - timedelta(hours=12))
        score = policy.age_score(e)
        assert 0.0 <= score <= 1.0

    def test_aging_policy_apply(self) -> None:
        policy = AgingPolicy(threshold_days=1)
        old = _make_entry("old", ts=datetime.now() - timedelta(days=10))
        result = policy.apply(old)
        assert result.status == MemoryStatus.ARCHIVED

    def test_forgetting_soft_deletes(self) -> None:
        engine = DefaultForgettingEngine(quality_threshold=0.9)
        store = InMemoryMemoryStore()
        e = _make_entry("low", quality=0.2)
        store.store(e)
        engine.apply_policies(store)
        retrieved = store.retrieve("low")
        assert retrieved is not None
        assert retrieved.status == MemoryStatus.ARCHIVED

    def test_forgetting_archives_not_deletes(self) -> None:
        engine = DefaultForgettingEngine(quality_threshold=0.9)
        store = InMemoryMemoryStore()
        e = _make_entry("to-archive", quality=0.1)
        store.store(e)
        engine.apply_policies(store)
        retrieved = store.retrieve("to-archive")
        assert retrieved is not None
        assert retrieved.status == MemoryStatus.ARCHIVED

    def test_forgetting_skips_disabled(self) -> None:
        engine = DefaultForgettingEngine(enabled=False)
        store = InMemoryMemoryStore()
        old = _make_entry("old", quality=0.1, ts=datetime.now() - timedelta(days=100))
        store.store(old)
        affected = engine.apply_policies(store)
        assert affected == []
