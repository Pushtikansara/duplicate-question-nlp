from __future__ import annotations

import logging
from typing import Any

from duplicate_question_app._memory.interfaces import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryStatistics,
    MemoryType,
)
from duplicate_question_app._memory.knowledge_graph import KnowledgeGraph
from duplicate_question_app._memory.memory_configuration import MemoryConfig
from duplicate_question_app._memory.memory_engine import MemoryEngine
from duplicate_question_app._memory.memory_query import MemoryQueryBuilder
from duplicate_question_app._memory.memory_result import ConsolidationResult, DeleteResult, StoreResult
from duplicate_question_app._memory.memory_types import (
    create_debate_memory,
    create_episodic_memory,
    create_performance_memory,
    create_reasoning_memory,
    create_semantic_memory,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(
        self,
        engine: MemoryEngine | None = None,
        config: MemoryConfig | None = None,
    ) -> None:
        self._engine = engine or MemoryEngine(config=config)

    @property
    def engine(self) -> MemoryEngine:
        return self._engine

    def store_episodic(
        self,
        question_a: str,
        question_b: str,
        pipeline_used: str,
        decision: str,
        confidence: float,
        latency_ms: float,
        **kwargs: Any,
    ) -> StoreResult:
        entry = create_episodic_memory(
            question_a=question_a,
            question_b=question_b,
            pipeline_used=pipeline_used,
            decision=decision,
            confidence=confidence,
            latency_ms=latency_ms,
            reasoning_summary=kwargs.get("reasoning_summary", ""),
            debate_summary=kwargs.get("debate_summary", ""),
            metadata=kwargs.get("metadata"),
        )
        return self._engine.store(entry)

    def store_semantic(
        self,
        concepts: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        intent_pattern: str,
        **kwargs: Any,
    ) -> StoreResult:
        entry = create_semantic_memory(
            concepts=concepts,
            entities=entities,
            relations=relations,
            intent_pattern=intent_pattern,
            semantic_graph=kwargs.get("semantic_graph"),
            confidence=kwargs.get("confidence", 0.8),
            metadata=kwargs.get("metadata"),
        )
        return self._engine.store(entry)

    def store_reasoning(
        self,
        reasoning_graph: dict[str, Any],
        premises: list[dict[str, Any]],
        evidence_chains: list[dict[str, Any]],
        hypotheses: list[dict[str, Any]],
        confidence_chain: dict[str, Any],
        reasoning_trace: dict[str, Any],
        **kwargs: Any,
    ) -> StoreResult:
        entry = create_reasoning_memory(
            reasoning_graph=reasoning_graph,
            premises=premises,
            evidence_chains=evidence_chains,
            hypotheses=hypotheses,
            confidence_chain=confidence_chain,
            reasoning_trace=reasoning_trace,
            confidence=kwargs.get("confidence", 0.8),
            metadata=kwargs.get("metadata"),
        )
        return self._engine.store(entry)

    def store_debate(
        self,
        agent_results: list[dict[str, Any]],
        votes: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
        consensus: dict[str, Any],
        disagreements: list[str],
        confidence_distribution: dict[str, Any],
        **kwargs: Any,
    ) -> StoreResult:
        entry = create_debate_memory(
            agent_results=agent_results,
            votes=votes,
            conflicts=conflicts,
            consensus=consensus,
            disagreements=disagreements,
            confidence_distribution=confidence_distribution,
            confidence=kwargs.get("confidence", 0.8),
            metadata=kwargs.get("metadata"),
        )
        return self._engine.store(entry)

    def store_performance(
        self,
        latency_ms: float,
        pipeline_cost: float,
        routing_decision: str,
        memory_hit_rate: float,
        **kwargs: Any,
    ) -> StoreResult:
        entry = create_performance_memory(
            latency_ms=latency_ms,
            pipeline_cost=pipeline_cost,
            routing_decision=routing_decision,
            memory_hit_rate=memory_hit_rate,
            cache_statistics=kwargs.get("cache_statistics"),
            execution_metrics=kwargs.get("execution_metrics"),
            confidence=kwargs.get("confidence", 1.0),
            metadata=kwargs.get("metadata"),
        )
        return self._engine.store(entry)

    def retrieve(self, memory_id: str) -> MemoryEntry | None:
        return self._engine.retrieve(memory_id)

    def search(self, query: MemoryQuery) -> MemoryResult:
        return self._engine.search(query)

    def search_by_type(self, memory_type: MemoryType, limit: int = 100) -> MemoryResult:
        query = MemoryQueryBuilder.by_type(memory_type, limit=limit)
        return self._engine.search(query)

    def search_by_tags(self, tags: list[str], limit: int = 100) -> MemoryResult:
        query = MemoryQueryBuilder.by_tags(tags, limit=limit)
        return self._engine.search(query)

    def search_text(self, text: str, limit: int = 100) -> MemoryResult:
        query = MemoryQueryBuilder.text_search(text, limit=limit)
        return self._engine.search(query)

    def delete(self, memory_id: str, soft: bool = True) -> DeleteResult:
        return self._engine.delete(memory_id, soft=soft)

    def consolidate(self) -> ConsolidationResult:
        return self._engine.consolidate()

    def get_statistics(self) -> MemoryStatistics:
        return self._engine.get_statistics()

    def get_knowledge_graph(self) -> KnowledgeGraph:
        return self._engine.graph

    def build_knowledge_graph(self, memory_types: list[MemoryType] | None = None) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        query = (
            MemoryQueryBuilder.by_type(memory_types[0])
            if memory_types and len(memory_types) == 1
            else MemoryQuery(limit=10000)
        )
        if memory_types:
            query.memory_types = memory_types
        result = self._engine.search(query)
        graph.build_from_memory(result.entries)
        return graph

    def audit_history(self, memory_id: str) -> list[dict[str, Any]]:
        return self._engine._audit.get_history(memory_id)

    def recent_audit_actions(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._engine._audit.get_recent_actions(limit=limit)
