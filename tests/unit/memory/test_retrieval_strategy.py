from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryType

from .conftest import RetrievalStrategy, get_retrieval_function


class TestRetrievalStrategy:
    def test_strategy_enum_values(self) -> None:
        assert RetrievalStrategy.EXACT.value == "exact"
        assert RetrievalStrategy.SEMANTIC.value == "semantic"
        assert RetrievalStrategy.HYBRID.value == "hybrid"

    def test_strategy_selector_exact(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.EXACT)
        assert callable(func)

    def test_strategy_selector_semantic(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.SEMANTIC)
        assert callable(func)

    def test_strategy_selector_hybrid(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.HYBRID)
        assert callable(func)

    def test_strategy_selector_default(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.EXACT)
        assert callable(func)

    def test_get_retrieval_function(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.EXACT)
        from duplicate_question_app._memory.interfaces import MemoryQuery
        from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

        store = InMemoryMemoryStore()
        query = MemoryQuery()
        result = func(query, store, None, None)
        assert result.entries == []

    def test_get_retrieval_function_all_types(self) -> None:
        for strategy in RetrievalStrategy:
            func = get_retrieval_function(strategy)
            assert callable(func)

    def test_strategy_selector_with_query_type(self) -> None:
        func = get_retrieval_function(RetrievalStrategy.EXACT)
        from duplicate_question_app._memory.interfaces import MemoryQuery
        from duplicate_question_app._memory.memory_store import InMemoryMemoryStore

        from .conftest import create_episodic_memory

        store = InMemoryMemoryStore()
        store.store(create_episodic_memory())
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC])
        result = func(query, store, None, None)
        assert result.total_count == 1

    def test_strategy_selector_fallback(self) -> None:
        from .conftest import RetrievalStrategy

        func = get_retrieval_function(RetrievalStrategy.EXACT)
        assert callable(func)

    def test_strategy_comparison(self) -> None:
        strategies = list(RetrievalStrategy)
        assert len(strategies) == 3
        assert RetrievalStrategy.EXACT != RetrievalStrategy.SEMANTIC
        assert RetrievalStrategy.SEMANTIC != RetrievalStrategy.HYBRID
