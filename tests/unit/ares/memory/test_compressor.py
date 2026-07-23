from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ares.memory import MemoryDomain, MemoryEntry, MemoryTier


class TestMemoryCompressor:
    def test_compress_working_to_short_term(self, memory_compressor) -> None:
        entries = [
            MemoryEntry(
                memory_id="w1",
                key="wk",
                value="wv",
                tier=MemoryTier.WORKING,
                domain=MemoryDomain.SEMANTIC,
                score=0.8,
            )
        ]
        promoted = memory_compressor.compress_working_to_short_term(entries)
        assert len(promoted) == 1
        assert promoted[0].tier == MemoryTier.SHORT_TERM
        assert promoted[0].version == 2
        assert promoted[0].ttl_seconds == 3600.0

    def test_compress_short_to_long_term(self, memory_compressor) -> None:
        entries = [
            MemoryEntry(
                memory_id="s1",
                key="sk",
                value="sv",
                tier=MemoryTier.SHORT_TERM,
                domain=MemoryDomain.SEMANTIC,
                score=0.9,
            )
        ]
        consolidated = memory_compressor.compress_short_to_long_term(entries)
        assert len(consolidated) == 1
        assert consolidated[0].tier == MemoryTier.LONG_TERM
        assert consolidated[0].ttl_seconds is None

    def test_compress_episodic_to_semantic(self, memory_compressor) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=10)
        entries = [
            MemoryEntry(
                memory_id="e1",
                key="ep",
                value="ev",
                tier=MemoryTier.SHORT_TERM,
                domain=MemoryDomain.EPISODIC,
                timestamp=old,
            )
        ]
        semantic = memory_compressor.compress_episodic_to_semantic(entries, max_age_hours=48.0)
        assert len(semantic) == 1
        assert semantic[0].domain == MemoryDomain.SEMANTIC

    def test_compress_episodic_too_recent(self, memory_compressor) -> None:
        recent = datetime.now(timezone.utc)
        entries = [
            MemoryEntry(
                memory_id="e2",
                key="ep2",
                value="ev2",
                tier=MemoryTier.SHORT_TERM,
                domain=MemoryDomain.EPISODIC,
                timestamp=recent,
            )
        ]
        semantic = memory_compressor.compress_episodic_to_semantic(entries, max_age_hours=48.0)
        assert len(semantic) == 0

    def test_prune_expired(self, memory_compressor) -> None:
        from datetime import datetime, timedelta, timezone

        fresh = MemoryEntry(
            memory_id="f1",
            key="fk",
            value="fv",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
        )
        expired_entry = MemoryEntry(
            memory_id="x1",
            key="xk",
            value="xv",
            tier=MemoryTier.WORKING,
            domain=MemoryDomain.SEMANTIC,
            ttl_seconds=3600,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        pruned = memory_compressor.prune_expired([fresh, expired_entry])
        assert len(pruned) == 1
        assert pruned[0].memory_id == "f1"
