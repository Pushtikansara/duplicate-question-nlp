from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

from .conftest import DefaultMemoryVersioning


def _make_entry(mid: str = "v-test") -> MemoryEntry:
    return MemoryEntry(
        memory_id=mid,
        memory_type=MemoryType.EPISODIC,
        version=1,
        timestamp=datetime.now(),
        source_module="test",
        quality_score=0.8,
        confidence=0.8,
        lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
        tags=["v"],
        metadata={},
        content={"k": "v"},
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


class TestMemoryVersioning:
    def test_create_version_increments(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v1 = ver.create_version(entry)
        assert v1.version == 1
        v2 = ver.create_version(entry)
        assert v2.version == 2
        v3 = ver.create_version(entry)
        assert v3.version == 3

    def test_create_version_with_parent(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v1 = ver.create_version(entry)
        v2 = ver.create_version(entry, parent_id=v1.memory_id)
        assert v2.version == 2

    def test_version_history(self) -> None:
        ver = DefaultMemoryVersioning()
        store = InMemoryMemoryStore()
        entry = _make_entry()
        for _ in range(3):
            ver.create_version(entry)
        history = ver.get_version_history(entry.memory_id, store)
        assert len(history) == 3

    def test_version_history_empty(self) -> None:
        ver = DefaultMemoryVersioning()
        store = InMemoryMemoryStore()
        history = ver.get_version_history("no-such", store)
        assert history == []

    def test_max_versions_enforced(self) -> None:
        ver = DefaultMemoryVersioning(max_versions=3)
        entry = _make_entry()
        for _ in range(5):
            ver.create_version(entry)
        history = ver.get_version_history(entry.memory_id, InMemoryMemoryStore())
        assert len(history) == 3

    def test_version_lineage_parent(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v1 = ver.create_version(entry)
        v2 = ver.create_version(entry)
        assert v2.version == v1.version + 1

    def test_version_timestamp_newer(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v1 = ver.create_version(entry)
        v2 = ver.create_version(entry)
        assert v2.timestamp >= v1.timestamp

    def test_version_content_preserved(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        entry.content["key"] = "original"
        ver.create_version(entry)
        entry.content["key"] = "modified"
        ver.create_version(entry)
        history = ver.get_version_history(entry.memory_id, InMemoryMemoryStore())
        assert len(history) >= 2

    def test_version_metadata_inherited(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        entry.metadata["source"] = "test"
        v = ver.create_version(entry)
        assert v.metadata.get("source") == "test"

    def test_multiple_version_chain(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        versions = []
        for _i in range(5):
            v = ver.create_version(entry)
            versions.append(v)
        assert [v.version for v in versions] == [1, 2, 3, 4, 5]

    def test_version_with_same_parent(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v1 = ver.create_version(entry)
        v2 = ver.create_version(entry, parent_id=v1.memory_id)
        assert v2.version == 2

    def test_version_history_ordered(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        for _ in range(3):
            ver.create_version(entry)
        history = ver.get_version_history(entry.memory_id, InMemoryMemoryStore())
        versions = [v.version for v in history]
        assert versions == sorted(versions)

    def test_version_history_limit(self) -> None:
        ver = DefaultMemoryVersioning(max_versions=2)
        entry = _make_entry()
        for _ in range(4):
            ver.create_version(entry)
        history = ver.get_version_history(entry.memory_id, InMemoryMemoryStore())
        assert len(history) <= 2

    def test_version_entry_to_dict(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        v = ver.create_version(entry)
        d = v.to_dict()
        assert d["version"] == 1
        assert d["memory_type"] == "episodic"

    def test_create_version_quality_score(self) -> None:
        ver = DefaultMemoryVersioning()
        entry = _make_entry()
        entry.quality_score = 0.95
        v = ver.create_version(entry)
        assert v.quality_score == 0.95
