from __future__ import annotations

from datetime import datetime

from duplicate_question_app._memory.memory_metadata import MemoryMetadata, MetadataFactory


class TestMemoryMetadata:
    def test_create_metadata(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        assert meta.access_count == 0
        assert meta.usage_frequency == 0.0
        assert meta.last_access is None

    def test_create_metadata_defaults(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        assert meta.access_count == 0
        assert meta.usage_frequency == 0.0

    def test_update_metadata(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        updated = MetadataFactory.update(meta)
        assert updated.access_count == 1
        assert updated.last_access is not None

    def test_update_increments_access_count(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        for _ in range(5):
            meta = MetadataFactory.update(meta)
        assert meta.access_count == 5

    def test_metadata_to_dict(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(
            created_at=now,
            updated_at=now,
            access_count=3,
            last_access=now,
            usage_frequency=0.5,
        )
        d = meta.to_dict()
        assert d["access_count"] == 3
        assert d["usage_frequency"] == 0.5
        assert "created_at" in d
        assert "updated_at" in d

    def test_factory_create(self) -> None:
        meta = MetadataFactory.create()
        assert meta.access_count == 0
        assert meta.usage_frequency == 0.0
        assert meta.last_access is None

    def test_factory_update(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now, access_count=10, usage_frequency=0.8)
        updated = MetadataFactory.update(meta)
        assert updated.access_count == 11
        assert updated.usage_frequency >= 0.0

    def test_usage_frequency_calculation(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        updated = MetadataFactory.update(meta)
        assert updated.usage_frequency >= 0.0

    def test_last_access_updated(self) -> None:
        meta = MetadataFactory.create()
        assert meta.last_access is None
        updated = MetadataFactory.update(meta)
        assert updated.last_access is not None

    def test_metadata_immutable_fields(self) -> None:
        now = datetime.now()
        meta = MemoryMetadata(created_at=now, updated_at=now)
        updated = MetadataFactory.update(meta)
        assert updated.created_at == meta.created_at
