from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType

from .conftest import MemoryLineageTracker


def _make_lineage_entry(
    mid: str,
    parent_ids: list[str] | None = None,
    module_chain: list[str] | None = None,
    reasoning_id: str | None = None,
    debate_id: str | None = None,
    created_by: str = "test",
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=mid,
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=datetime.now(),
        source_module="test",
        quality_score=0.8,
        confidence=0.8,
        lineage=MemoryLineage(
            created_by=created_by,
            created_at=datetime.now(),
            parent_ids=parent_ids or [],
            module_chain=module_chain or [],
            reasoning_id=reasoning_id,
            debate_id=debate_id,
        ),
        tags=["lineage"],
        metadata={},
        content={"k": "v"},
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


class TestMemoryLineage:
    def test_track_lineage(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("e1")
        tracker.track(e)
        ancestors = tracker.get_ancestors("e1")
        assert ancestors == []

    def test_get_ancestors(self) -> None:
        tracker = MemoryLineageTracker()
        parent = _make_lineage_entry("parent")
        child = _make_lineage_entry("child", parent_ids=["parent"])
        tracker.track(parent)
        tracker.track(child)
        ancestors = tracker.get_ancestors("child")
        assert len(ancestors) == 1
        assert ancestors[0].memory_id == "parent"

    def test_get_ancestors_no_parents(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("orphan")
        tracker.track(e)
        assert tracker.get_ancestors("orphan") == []

    def test_get_descendants(self) -> None:
        tracker = MemoryLineageTracker()
        parent = _make_lineage_entry("parent")
        child = _make_lineage_entry("child", parent_ids=["parent"])
        tracker.track(parent)
        tracker.track(child)
        descendants = tracker.get_descendants("parent")
        assert len(descendants) == 1
        assert descendants[0].memory_id == "child"

    def test_get_descendants_none(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("leaf")
        tracker.track(e)
        assert tracker.get_descendants("leaf") == []

    def test_merge_lineages(self) -> None:
        tracker = MemoryLineageTracker()
        la = MemoryLineage(
            created_by="alice",
            created_at=datetime.now(),
            parent_ids=["p1"],
            module_chain=["m1"],
        )
        lb = MemoryLineage(
            created_by="bob",
            created_at=datetime.now(),
            parent_ids=["p2"],
            module_chain=["m2"],
        )
        merged = tracker.merge_lineages(la, lb)
        assert "p1" in merged.parent_ids
        assert "p2" in merged.parent_ids
        assert "m1" in merged.module_chain
        assert "m2" in merged.module_chain

    def test_merge_lineages_single(self) -> None:
        tracker = MemoryLineageTracker()
        la = MemoryLineage(created_by="alice", created_at=datetime.now())
        merged = tracker.merge_lineages(la, la)
        assert merged.created_by == "alice"

    def test_merge_lineages_multiple(self) -> None:
        tracker = MemoryLineageTracker()
        la = MemoryLineage(
            created_by="a",
            created_at=datetime.now(),
            parent_ids=["p1", "p2"],
            module_chain=["m1"],
        )
        lb = MemoryLineage(
            created_by="b",
            created_at=datetime.now(),
            parent_ids=["p2", "p3"],
            module_chain=["m2"],
        )
        merged = tracker.merge_lineages(la, lb)
        assert sorted(merged.parent_ids) == sorted(["p1", "p2", "p3"])
        assert len(merged.module_chain) == 2

    def test_lineage_module_chain(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("e1", module_chain=["pipeline", "semantic", "reasoning"])
        tracker.track(e)
        ancestors = tracker.get_ancestors("e1")
        assert ancestors == []

    def test_lineage_reasoning_id(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("e1", reasoning_id="reason-abc")
        tracker.track(e)
        assert e.lineage.reasoning_id == "reason-abc"

    def test_lineage_debate_id(self) -> None:
        tracker = MemoryLineageTracker()
        e = _make_lineage_entry("e1", debate_id="debate-xyz")
        tracker.track(e)
        assert e.lineage.debate_id == "debate-xyz"

    def test_lineage_to_dict(self) -> None:
        lineage = MemoryLineage(
            created_by="test-user",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            parent_ids=["p1"],
            module_chain=["m1"],
            reasoning_id="r1",
            debate_id="d1",
        )
        d = lineage.to_dict()
        assert d["created_by"] == "test-user"
        assert "p1" in d["parent_ids"]
        assert d["reasoning_id"] == "r1"

    def test_multiple_generations(self) -> None:
        tracker = MemoryLineageTracker()
        g1 = _make_lineage_entry("g1")
        g2 = _make_lineage_entry("g2", parent_ids=["g1"])
        g3 = _make_lineage_entry("g3", parent_ids=["g2"])
        for e in [g1, g2, g3]:
            tracker.track(e)
        ancestors_g3 = tracker.get_ancestors("g3")
        assert len(ancestors_g3) == 2
        assert ancestors_g3[0].memory_id == "g2"
        assert ancestors_g3[1].memory_id == "g1"

    def test_lineage_created_by(self) -> None:
        e = _make_lineage_entry("e1", created_by="special-user")
        assert e.lineage.created_by == "special-user"

    def test_ancestors_ordered_by_version(self) -> None:
        tracker = MemoryLineageTracker()
        parent = _make_lineage_entry("parent")
        child = _make_lineage_entry("child", parent_ids=["parent"])
        tracker.track(parent)
        tracker.track(child)
        ancestors = tracker.get_ancestors("child")
        assert len(ancestors) == 1
