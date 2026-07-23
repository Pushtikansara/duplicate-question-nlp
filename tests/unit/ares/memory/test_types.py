from __future__ import annotations

from ares.memory import (
    MemoryDomain,
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryStats,
    MemoryTier,
    MemoryValue,
)


class TestMemoryTier:
    def test_tier_values(self) -> None:
        assert MemoryTier.WORKING.name == "WORKING"
        assert MemoryTier.SHORT_TERM.name == "SHORT_TERM"
        assert MemoryTier.LONG_TERM.name == "LONG_TERM"

    def test_tier_count(self) -> None:
        assert len(MemoryTier) == 3


class TestMemoryDomain:
    def test_domain_values(self) -> None:
        assert MemoryDomain.EPISODIC.name == "EPISODIC"
        assert MemoryDomain.SEMANTIC.name == "SEMANTIC"
        assert MemoryDomain.REFLECTION.name == "REFLECTION"

    def test_domain_count(self) -> None:
        assert len(MemoryDomain) == 3


class TestMemoryValue:
    def test_create_memory_value(self, sample_memory_value: MemoryValue) -> None:
        assert sample_memory_value.key == "test_key"
        assert sample_memory_value.value == {"data": 42}
        assert sample_memory_value.tier == MemoryTier.WORKING
        assert sample_memory_value.domain == MemoryDomain.SEMANTIC

    def test_is_expired_no_ttl(self, sample_memory_value: MemoryValue) -> None:
        assert sample_memory_value.is_expired is False

    def test_is_expired_with_ttl(self) -> None:
        from datetime import datetime, timedelta, timezone

        past = datetime.now(timezone.utc) - timedelta(hours=2)
        mv = MemoryValue(key="k", value="v", ttl_seconds=3600, timestamp=past)
        assert mv.is_expired is True

    def test_is_expired_fresh(self) -> None:
        mv = MemoryValue(key="k", value="v", ttl_seconds=3600)
        assert mv.is_expired is False

    def test_default_values(self) -> None:
        mv = MemoryValue(key="k", value="v")
        assert mv.tier == MemoryTier.WORKING
        assert mv.domain == MemoryDomain.SEMANTIC
        assert mv.score == 1.0
        assert mv.access_count == 0


class TestMemoryEntry:
    def test_create_entry(self, sample_entry: MemoryEntry) -> None:
        assert sample_entry.memory_id == "entry-1"
        assert sample_entry.key == "test_key"
        assert sample_entry.value == {"data": 42}
        assert sample_entry.tier == MemoryTier.WORKING
        assert sample_entry.domain == MemoryDomain.SEMANTIC

    def test_is_expired(self) -> None:
        from datetime import datetime, timedelta, timezone

        past = datetime.now(timezone.utc) - timedelta(hours=2)
        entry = MemoryEntry(
            memory_id="e1",
            key="k",
            value="v",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            ttl_seconds=3600,
            timestamp=past,
        )
        assert entry.is_expired is True

    def test_version_default(self) -> None:
        entry = MemoryEntry(memory_id="e1", key="k", value="v", tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        assert entry.version == 1

    def test_tags_default(self) -> None:
        entry = MemoryEntry(memory_id="e1", key="k", value="v", tier=MemoryTier.WORKING, domain=MemoryDomain.SEMANTIC)
        assert entry.tags == []


class TestMemoryQuery:
    def test_default_query(self) -> None:
        q = MemoryQuery()
        assert q.key == ""
        assert q.tier is None
        assert q.domain is None
        assert q.limit == 100
        assert q.include_expired is False

    def test_query_with_filters(self) -> None:
        q = MemoryQuery(
            key="test",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            agent_id="agent-1",
            tags=["urgent"],
            min_score=0.5,
            limit=10,
        )
        assert q.key == "test"
        assert q.tier == MemoryTier.WORKING
        assert q.domain == MemoryDomain.SEMANTIC
        assert q.agent_id == "agent-1"
        assert q.tags == ["urgent"]
        assert q.min_score == 0.5
        assert q.limit == 10


class TestMemoryResult:
    def test_default_result(self) -> None:
        r = MemoryResult()
        assert r.entries == []
        assert r.total_count == 0
        assert r.query_time_ms == 0.0

    def test_result_with_entries(self, sample_entry: MemoryEntry) -> None:
        r = MemoryResult(entries=[sample_entry], total_count=1, query_time_ms=1.5)
        assert len(r.entries) == 1
        assert r.total_count == 1
        assert r.query_time_ms == 1.5


class TestMemoryStats:
    def test_default_stats(self) -> None:
        s = MemoryStats()
        assert s.total_entries == 0
        assert s.entries_by_tier == {}
        assert s.entries_by_domain == {}
        assert s.session_count == 0
