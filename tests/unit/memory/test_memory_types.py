from __future__ import annotations

from duplicate_question_app._memory.interfaces import MemoryLineage, MemoryType

from .conftest import (
    create_debate_memory,
    create_episodic_memory,
    create_performance_memory,
    create_reasoning_memory,
    create_semantic_memory,
)


class TestMemoryTypes:
    def test_create_episodic_memory(self) -> None:
        entry = create_episodic_memory()
        assert entry.memory_type == MemoryType.EPISODIC

    def test_create_episodic_memory_fields(self) -> None:
        entry = create_episodic_memory()
        assert "question_a" in entry.content
        assert "question_b" in entry.content
        assert "pipeline_used" in entry.content
        assert "decision" in entry.content

    def test_create_semantic_memory(self) -> None:
        entry = create_semantic_memory()
        assert entry.memory_type == MemoryType.SEMANTIC

    def test_create_semantic_memory_with_relations(self) -> None:
        entry = create_semantic_memory()
        assert "relations" in entry.content
        assert "concepts" in entry.content
        assert "entities" in entry.content

    def test_create_reasoning_memory(self) -> None:
        entry = create_reasoning_memory()
        assert entry.memory_type == MemoryType.REASONING

    def test_create_reasoning_memory_with_graph(self) -> None:
        entry = create_reasoning_memory()
        assert "reasoning_graph" in entry.content
        assert "premises" in entry.content
        assert "evidence_chains" in entry.content

    def test_create_debate_memory(self) -> None:
        entry = create_debate_memory()
        assert entry.memory_type == MemoryType.DEBATE

    def test_create_debate_memory_with_results(self) -> None:
        entry = create_debate_memory()
        assert "agent_results" in entry.content
        assert "votes" in entry.content
        assert "consensus" in entry.content

    def test_create_performance_memory(self) -> None:
        entry = create_performance_memory()
        assert entry.memory_type == MemoryType.PERFORMANCE

    def test_create_performance_memory_with_metrics(self) -> None:
        entry = create_performance_memory()
        assert "latency_ms" in entry.content
        assert "pipeline_cost" in entry.content
        assert "routing_decision" in entry.content

    def test_all_types_have_valid_ids(self) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            entry = c()
            assert entry.memory_id != ""
            assert isinstance(entry.memory_id, str)

    def test_all_types_have_version_1(self) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            entry = c()
            assert entry.version == 1

    def test_all_types_have_timestamps(self) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            entry = c()
            assert entry.timestamp is not None

    def test_all_types_have_lineage(self) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            entry = c()
            assert isinstance(entry.lineage, MemoryLineage)
            assert entry.lineage.created_by == "test"

    def test_all_types_have_quality_score(self) -> None:
        creators = [
            create_episodic_memory,
            create_semantic_memory,
            create_reasoning_memory,
            create_debate_memory,
            create_performance_memory,
        ]
        for c in creators:
            entry = c()
            assert 0.0 <= entry.quality_score <= 1.0

    def test_episodic_content_structure(self) -> None:
        entry = create_episodic_memory()
        assert isinstance(entry.content, dict)
        for field in ("question_a", "question_b", "pipeline_used", "decision"):
            assert field in entry.content

    def test_semantic_content_structure(self) -> None:
        entry = create_semantic_memory()
        for field in ("concepts", "entities", "relations", "intent_pattern"):
            assert field in entry.content

    def test_reasoning_content_structure(self) -> None:
        entry = create_reasoning_memory()
        for field in (
            "reasoning_graph",
            "premises",
            "evidence_chains",
            "hypotheses",
            "confidence_chain",
            "reasoning_trace",
        ):
            assert field in entry.content

    def test_debate_content_structure(self) -> None:
        entry = create_debate_memory()
        for field in ("agent_results", "votes", "conflicts", "consensus", "disagreements", "confidence_distribution"):
            assert field in entry.content

    def test_performance_content_structure(self) -> None:
        entry = create_performance_memory()
        for field in ("latency_ms", "pipeline_cost", "routing_decision", "memory_hit_rate"):
            assert field in entry.content
