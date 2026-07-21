from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType
from duplicate_question_app._memory.memory_deserializer import MemoryDeserializer
from duplicate_question_app._memory.memory_serializer import MemorySerializer

from .conftest import (
    create_episodic_memory,
    create_semantic_memory,
)


class TestMemorySerializer:
    def test_serialize_episodic(self) -> None:
        entry = create_episodic_memory()
        data = MemorySerializer.serialize(entry)
        assert data["memory_type"] == "episodic"
        assert data["memory_id"] == entry.memory_id
        assert "lineage" in data

    def test_serialize_semantic(self) -> None:
        entry = create_semantic_memory()
        data = MemorySerializer.serialize(entry)
        assert data["memory_type"] == "semantic"
        assert data["version"] == 1

    def test_deserialize_episodic(self) -> None:
        entry = create_episodic_memory()
        data = MemorySerializer.serialize(entry)
        restored = MemoryDeserializer.deserialize(data)
        assert restored.memory_id == entry.memory_id
        assert restored.memory_type == MemoryType.EPISODIC
        assert restored.quality_score == entry.quality_score

    def test_serialize_deserialize_roundtrip(self) -> None:
        entry = create_episodic_memory(
            memory_id="roundtrip-test",
            tags=["a", "b"],
            metadata={"key": "val"},
            embedding=[0.1, 0.2, 0.3],
            expires_at=datetime.now() + timedelta(days=1),
        )
        data = MemorySerializer.serialize(entry)
        restored = MemoryDeserializer.deserialize(data)
        assert restored.memory_id == "roundtrip-test"
        assert restored.tags == ["a", "b"]
        assert restored.metadata == {"key": "val"}
        assert restored.embedding == [0.1, 0.2, 0.3]
        assert restored.expires_at is not None

    def test_serialize_batch(self) -> None:
        entries = [create_episodic_memory(), create_semantic_memory()]
        data_list = MemorySerializer.serialize_batch(entries)
        assert len(data_list) == 2

    def test_deserialize_batch(self) -> None:
        entries = [create_episodic_memory(), create_semantic_memory()]
        data_list = MemorySerializer.serialize_batch(entries)
        restored = MemoryDeserializer.deserialize_batch(data_list)
        assert len(restored) == 2
        assert restored[0].memory_type == MemoryType.EPISODIC
        assert restored[1].memory_type == MemoryType.SEMANTIC

    def test_serialize_with_embedding(self) -> None:
        entry = create_episodic_memory(embedding=[0.5, 0.6, 0.7, 0.8])
        data = MemorySerializer.serialize(entry)
        assert data["embedding"] == [0.5, 0.6, 0.7, 0.8]
        restored = MemoryDeserializer.deserialize(data)
        assert restored.embedding == [0.5, 0.6, 0.7, 0.8]

    def test_serialize_with_expires(self) -> None:
        expires = datetime.now() + timedelta(hours=48)
        entry = create_episodic_memory(expires_at=expires)
        data = MemorySerializer.serialize(entry)
        assert data["expires_at"] is not None
        restored = MemoryDeserializer.deserialize(data)
        assert restored.expires_at is not None

    def test_deserialize_preserves_all_fields(self) -> None:
        lineage = MemoryLineage(
            created_by="user1",
            created_at=datetime(2024, 6, 1, 12, 0, 0),
            parent_ids=["p1"],
            module_chain=["m1", "m2"],
            reasoning_id="r1",
            debate_id="d1",
        )
        entry = MemoryEntry(
            memory_id="full-test",
            memory_type=MemoryType.PERFORMANCE,
            version=3,
            timestamp=datetime(2024, 6, 15, 10, 30, 0),
            source_module="monitor",
            quality_score=0.92,
            confidence=0.88,
            lineage=lineage,
            tags=["perf", "test"],
            metadata={"host": "srv-01"},
            content={"latency_ms": 120, "pipeline_cost": 0.03, "routing_decision": "auto", "memory_hit_rate": 0.9},
            embedding=[0.01, 0.02],
            expires_at=datetime(2025, 1, 1, 0, 0, 0),
            status=MemoryStatus.ACTIVE,
        )
        data = MemorySerializer.serialize(entry)
        restored = MemoryDeserializer.deserialize(data)
        assert restored.memory_id == "full-test"
        assert restored.memory_type == MemoryType.PERFORMANCE
        assert restored.version == 3
        assert restored.quality_score == 0.92
        assert restored.lineage.reasoning_id == "r1"
        assert restored.status == MemoryStatus.ACTIVE

    def test_serialize_empty_batch(self) -> None:
        data_list = MemorySerializer.serialize_batch([])
        assert data_list == []
