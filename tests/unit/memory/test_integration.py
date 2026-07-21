from __future__ import annotations

from datetime import datetime, timedelta

from duplicate_question_app._memory.interfaces import (
    MemoryEntry,
    MemoryLineage,
    MemoryQuery,
    MemoryStatus,
    MemoryType,
)
from duplicate_question_app._memory.memory_configuration import MemoryConfig
from duplicate_question_app._memory.memory_deserializer import MemoryDeserializer
from duplicate_question_app._memory.memory_serializer import MemorySerializer
from duplicate_question_app._memory.plugins import DefaultMemoryPlugin

from .conftest import (
    AgingPolicy,
    DefaultForgettingEngine,
    MemoryEngine,
    MemoryManager,
    MemoryQualityScorer,
    create_debate_memory,
    create_episodic_memory,
    create_performance_memory,
    create_reasoning_memory,
    create_semantic_memory,
)


class TestIntegration:
    def test_store_retrieve_all_types(self, memory_engine: MemoryEngine) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        stored_ids = []
        for c in creators:
            result = memory_engine.store_entry(c())
            stored_ids.append(result.memory_id)
        for mid in stored_ids:
            retrieved = memory_engine.retrieve(mid)
            assert retrieved is not None
        stats = memory_engine.get_statistics()
        assert stats.total_entries == 5

    def test_store_then_search_then_delete(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory(tags=["lifecycle"], source_module="integration")
        result = memory_engine.store_entry(entry)
        query = MemoryQuery(tags=["lifecycle"])
        search_result = memory_engine.search(query)
        assert search_result.total_count == 1
        memory_engine.delete(result.memory_id, soft=True)
        search_after = memory_engine.search(query)
        assert search_after.total_count == 0

    def test_store_then_update_then_retrieve(self, memory_engine: MemoryEngine) -> None:
        entry = create_episodic_memory(quality_score=0.5)
        result = memory_engine.store_entry(entry)
        entry.memory_id = result.memory_id
        entry.quality_score = 0.95
        memory_engine.update(entry)
        retrieved = memory_engine.retrieve(result.memory_id)
        assert retrieved is not None
        assert retrieved.quality_score == 0.95

    def test_full_episodic_lifecycle(self) -> None:
        engine = MemoryEngine()
        entry = create_episodic_memory(
            memory_id="lifecycle-epi-1",
            tags=["episodic", "qa"],
        )
        store_result = engine.store_entry(entry)
        assert store_result.success is True
        retrieved = engine.retrieve(store_result.memory_id)
        assert retrieved is not None
        assert retrieved.memory_type == MemoryType.EPISODIC
        retrieve_again = engine.retrieve(store_result.memory_id)
        assert retrieve_again is not None
        delete_result = engine.delete(store_result.memory_id, soft=True)
        assert delete_result.success is True
        after_delete = engine.retrieve(store_result.memory_id)
        assert after_delete is not None
        assert after_delete.status == MemoryStatus.DELETED

    def test_full_semantic_lifecycle(self) -> None:
        engine = MemoryEngine()
        entry = create_semantic_memory(memory_id="")
        store_result = engine.store_entry(entry)
        assert store_result.success is True
        query = MemoryQuery(memory_types=[MemoryType.SEMANTIC])
        results = engine.search(query)
        assert results.total_count == 1
        engine.delete(store_result.memory_id, soft=True)
        results_after = engine.search(query)
        assert results_after.total_count == 0

    def test_storage_then_consolidation(self) -> None:
        engine = MemoryEngine()
        content = {"question_a": "DupQ", "question_b": "DupQ2", "pipeline_used": "p", "decision": "d"}
        e1 = create_episodic_memory(tags=["dup-group"], content=content)
        e2 = create_episodic_memory(tags=["dup-group"], content=content)
        engine.store_entry(e1)
        engine.store_entry(e2)
        result = engine.consolidate()
        assert len(result.merged_ids) >= 1

    def test_versioning_with_updates(self) -> None:
        engine = MemoryEngine()
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        history = engine.get_version_history(result.memory_id)
        assert len(history) == 1
        entry.memory_id = result.memory_id
        entry.content["decision"] = "updated"
        engine.update(entry)
        history = engine.get_version_history(result.memory_id)
        assert len(history) >= 1

    def test_audit_trail(self) -> None:
        engine = MemoryEngine()
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        engine.retrieve(result.memory_id)
        engine.retrieve(result.memory_id)
        history = engine.audit.get_history(result.memory_id)
        assert len(history) == 3
        actions = [h["action"] for h in history]
        assert actions.count("retrieve") == 2
        assert actions.count("store") == 1

    def test_knowledge_graph_build(self) -> None:
        manager = MemoryManager()
        for _ in range(3):
            manager.store_episodic()
        manager.store_semantic()
        kg = manager.build_knowledge_graph()
        assert len(kg.to_dict()["nodes"]) == 4

    def test_forgetting_cycle(self) -> None:
        engine = MemoryEngine(
            forgetting=DefaultForgettingEngine(
                aging_policy=AgingPolicy(threshold_days=1),
                quality_threshold=0.9,
            )
        )
        old_entry = MemoryEntry(
            memory_id="old-entry",
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=datetime.now() - timedelta(days=30),
            source_module="test",
            quality_score=0.2,
            confidence=0.2,
            lineage=MemoryLineage(created_by="test", created_at=datetime.now()),
            tags=["old"],
            metadata={},
            content={"question_a": "Q", "question_b": "Q2", "pipeline_used": "p", "decision": "d"},
        )
        engine.store_entry(old_entry)
        affected = engine.apply_forgetting()
        assert "old-entry" in affected
        retrieved = engine.retrieve("old-entry")
        assert retrieved is not None
        assert retrieved.status == MemoryStatus.ARCHIVED

    def test_memory_quality_over_time(self) -> None:
        scorer = MemoryQualityScorer()
        entry = create_episodic_memory(confidence=0.9, quality_score=0.85)
        score1 = scorer.score(entry)
        entry.confidence = 0.5
        score2 = scorer.score(entry)
        assert score2 <= score1

    def test_concurrent_read_write(self) -> None:
        import threading

        engine = MemoryEngine()
        errors: list[Exception] = []
        lock = threading.Lock()

        def _worker() -> None:
            try:
                for _ in range(20):
                    e = create_episodic_memory()
                    r = engine.store_entry(e)
                    engine.retrieve(r.memory_id)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        stats = engine.get_statistics()
        assert stats.total_entries == 100

    def test_large_volume_storage(self) -> None:
        engine = MemoryEngine()
        for i in range(100):
            e = create_episodic_memory(
                memory_id=f"vol-{i}",
                content={"question_a": f"Q{i}", "question_b": f"Q{i}b", "pipeline_used": "p", "decision": "d"},
            )
            engine.store_entry(e)
        stats = engine.get_statistics()
        assert stats.total_entries == 100
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        results = engine.search(query)
        assert results.total_count == 100

    def test_cross_type_search(self) -> None:
        engine = MemoryEngine()
        engine.store_entry(create_episodic_memory(tags=["shared-tag"]))
        engine.store_entry(create_semantic_memory(tags=["shared-tag"]))
        engine.store_entry(create_reasoning_memory(tags=["shared-tag"]))
        query = MemoryQuery(tags=["shared-tag"])
        results = engine.search(query)
        assert results.total_count == 3

    def test_engine_manager_integration(self) -> None:
        manager = MemoryManager()
        for _ in range(3):
            manager.store_episodic()
        manager.store_semantic()
        stats = manager.get_statistics()
        assert stats.total_entries == 4
        kg = manager.build_knowledge_graph()
        assert kg.get_node(list(kg.to_dict()["nodes"])[0]["id"]) is not None

    def test_serialize_deserialize_cycle(self) -> None:
        entry = create_episodic_memory(
            memory_id="serial-cycle",
            tags=["ser", "deser"],
            embedding=[0.1, 0.2],
        )
        data = MemorySerializer.serialize(entry)
        restored = MemoryDeserializer.deserialize(data)
        assert restored.memory_id == "serial-cycle"
        assert restored.tags == ["ser", "deser"]
        assert restored.embedding == [0.1, 0.2]
        data2 = MemorySerializer.serialize(restored)
        assert data == data2

    def test_config_affects_behavior(self) -> None:
        config = MemoryConfig(max_versions=3)
        engine = MemoryEngine(config=config)
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        entry.memory_id = result.memory_id
        for i in range(5):
            entry.content["iter"] = i
            engine.update(entry)
        history = engine.get_version_history(result.memory_id)
        assert len(history) <= 3

    def test_plugin_integration(self) -> None:
        class _TestPlugin(DefaultMemoryPlugin):
            def process_before_store(self, entry: MemoryEntry) -> MemoryEntry:
                entry.metadata["plugin_before"] = True
                return entry

            def process_after_retrieve(self, entry: MemoryEntry | None) -> MemoryEntry | None:
                if entry is not None:
                    entry.metadata["plugin_after"] = True
                return entry

        engine = MemoryEngine(plugins=[_TestPlugin()])
        entry = create_episodic_memory()
        result = engine.store_entry(entry)
        retrieved = engine.retrieve(result.memory_id)
        assert retrieved is not None
        assert retrieved.metadata.get("plugin_after") is True

    def test_statistics_after_complex_workflow(self) -> None:
        engine = MemoryEngine()
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            engine.store_entry(c())
        stats = engine.get_statistics()
        assert stats.total_entries == 5
        assert len(stats.total_by_type) == 5
        assert stats.avg_quality > 0.0
        assert stats.avg_confidence > 0.0

    def test_recovery_after_clear(self) -> None:
        engine = MemoryEngine()
        for _ in range(10):
            engine.store_entry(create_episodic_memory())
        assert engine.get_statistics().total_entries == 10
        engine._store.clear()
        stats = engine.get_statistics()
        assert stats.total_entries == 0
        new_entry = create_episodic_memory()
        result = engine.store_entry(new_entry)
        assert result.success is True
        assert engine.get_statistics().total_entries == 1
