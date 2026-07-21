from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryQuery, MemoryType
from duplicate_question_app._memory.memory_query import MemoryQueryBuilder


class TestMemoryQuery:
    def test_query_builder_by_type(self) -> None:
        query = MemoryQueryBuilder.by_type(MemoryType.EPISODIC)
        assert query.memory_types == [MemoryType.EPISODIC]
        assert query.query_type == "exact"

    def test_query_builder_by_tags(self) -> None:
        query = MemoryQueryBuilder.by_tags(["tag1", "tag2"])
        assert query.tags == ["tag1", "tag2"]

    def test_query_builder_by_confidence(self) -> None:
        query = MemoryQueryBuilder.by_confidence(0.8)
        assert query.min_confidence == 0.8

    def test_query_builder_by_source(self) -> None:
        query = MemoryQueryBuilder.by_source("test_module")
        assert query.source_modules == ["test_module"]

    def test_query_builder_text_search(self) -> None:
        query = MemoryQueryBuilder.text_search("python")
        assert query.text == "python"
        assert query.query_type == "semantic"

    def test_query_builder_hybrid(self) -> None:
        query = MemoryQueryBuilder.hybrid("python", [MemoryType.EPISODIC])
        assert query.text == "python"
        assert query.memory_types == [MemoryType.EPISODIC]
        assert query.query_type == "hybrid"

    def test_query_default_values(self) -> None:
        query = MemoryQuery()
        assert query.query_type == "exact"
        assert query.memory_types is None
        assert query.tags is None
        assert query.limit == 100
        assert query.offset == 0
        assert query.min_confidence == 0.0
        assert query.min_quality == 0.0
        assert query.text == ""
        assert query.filters == {}

    def test_query_limit(self) -> None:
        query = MemoryQueryBuilder.by_type(MemoryType.EPISODIC, limit=10)
        assert query.limit == 10

    def test_query_offset(self) -> None:
        query = MemoryQuery(memory_types=[MemoryType.EPISODIC], offset=20)
        assert query.offset == 20

    def test_query_with_filters(self) -> None:
        query = MemoryQuery(
            memory_types=[MemoryType.SEMANTIC],
            filters={"domain": "science"},
        )
        assert query.filters == {"domain": "science"}

    def test_query_to_dict(self) -> None:
        query = MemoryQueryBuilder.by_type(MemoryType.PERFORMANCE, limit=5)
        d = query.to_dict()
        assert d["query_type"] == "exact"
        assert d["memory_types"] == ["performance"]
        assert d["limit"] == 5
