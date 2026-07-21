from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryQuery, MemoryType

from .conftest import (
    ConsolidationResult,
    DeleteResult,
    MemoryEngine,
    MemoryManager,
    StoreResult,
)


class TestMemoryManager:
    def test_store_episodic(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_episodic()
        assert isinstance(result, StoreResult)
        assert result.success is True

    def test_store_semantic(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_semantic()
        assert result.success is True

    def test_store_reasoning(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_reasoning()
        assert result.success is True

    def test_store_debate(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_debate()
        assert result.success is True

    def test_store_performance(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_performance()
        assert result.success is True

    def test_retrieve(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_episodic()
        retrieved = memory_manager.retrieve(result.memory_id)
        assert retrieved is not None
        assert retrieved.memory_type == MemoryType.EPISODIC

    def test_search(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic()
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = memory_manager.search(query)
        assert result.total_count >= 1

    def test_search_by_type(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic(tags=["st"])
        memory_manager.store_semantic(tags=["st2"])
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = memory_manager.search(query)
        assert result.total_count == 1

    def test_search_by_tags(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic(tags=["custom-search-tag"])
        query = MemoryQuery(tags=["custom-search-tag"])
        result = memory_manager.search(query)
        assert result.total_count == 1

    def test_search_text(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic(
            content={
                "question_a": "How to use Flask?",
                "question_b": "Using Flask framework",
                "pipeline_used": "test",
                "decision": "duplicate",
            }
        )
        query = MemoryQuery(text="Flask")
        result = memory_manager.search(query)
        assert result.total_count >= 1

    def test_delete(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_episodic()
        delete_result = memory_manager.delete(result.memory_id)
        assert isinstance(delete_result, DeleteResult)
        assert delete_result.success is True

    def test_consolidate(self, memory_manager: MemoryManager) -> None:
        content = {"question_a": "A", "question_b": "B", "pipeline_used": "p", "decision": "d"}
        memory_manager.store_episodic(tags=["mc"], content=content)
        memory_manager.store_episodic(tags=["mc"], content=content)
        result = memory_manager.consolidate()
        assert isinstance(result, ConsolidationResult)

    def test_get_statistics(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic()
        memory_manager.store_semantic()
        stats = memory_manager.get_statistics()
        assert stats.total_entries == 2

    def test_get_knowledge_graph(self, memory_manager: MemoryManager) -> None:
        kg = memory_manager.get_knowledge_graph()
        assert hasattr(kg, "get_node")
        assert hasattr(kg, "add_node")

    def test_build_knowledge_graph(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic()
        memory_manager.store_semantic()
        kg = memory_manager.build_knowledge_graph()
        assert hasattr(kg, "get_node")
        assert len(kg.to_dict()["nodes"]) == 2

    def test_build_knowledge_graph_filtered(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic()
        memory_manager.store_semantic()
        kg = memory_manager.build_knowledge_graph(memory_type=MemoryType.EPISODIC)
        assert len(kg.to_dict()["nodes"]) == 1

    def test_audit_history(self, memory_manager: MemoryManager) -> None:
        result = memory_manager.store_episodic()
        history = memory_manager.audit_history(result.memory_id)
        assert isinstance(history, list)
        assert len(history) >= 1

    def test_recent_audit_actions(self, memory_manager: MemoryManager) -> None:
        memory_manager.store_episodic()
        memory_manager.store_semantic()
        actions = memory_manager.recent_audit_actions()
        assert len(actions) >= 2

    def test_manager_default_engine(self) -> None:
        manager = MemoryManager()
        assert isinstance(manager.engine, MemoryEngine)

    def test_manager_custom_engine(self) -> None:
        engine = MemoryEngine()
        manager = MemoryManager(engine=engine)
        assert manager.engine is engine
