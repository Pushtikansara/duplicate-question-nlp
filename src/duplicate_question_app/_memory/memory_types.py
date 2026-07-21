from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryLineage, MemoryStatus, MemoryType


def _make_lineage(created_by: str = "memory_types") -> MemoryLineage:
    return MemoryLineage(
        created_by=created_by,
        created_at=datetime.now(),
        parent_ids=[],
        module_chain=["_memory"],
        reasoning_id=None,
        debate_id=None,
    )


def _compute_quality(confidence: float) -> float:
    return round(min(max(confidence * 0.9 + 0.1, 0.0), 1.0), 4)


def _make_entry(
    memory_type: MemoryType,
    content: dict[str, Any],
    tags: list[str],
    confidence: float,
    metadata: dict[str, Any] | None,
    lineage: MemoryLineage | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=str(uuid.uuid4()),
        memory_type=memory_type,
        version=1,
        timestamp=datetime.now(),
        source_module="_memory",
        quality_score=_compute_quality(confidence),
        confidence=confidence,
        lineage=lineage or _make_lineage(),
        tags=tags,
        metadata=metadata or {},
        content=content,
        embedding=None,
        expires_at=None,
        status=MemoryStatus.ACTIVE,
    )


def create_episodic_memory(
    question_a: str,
    question_b: str,
    pipeline_used: str,
    decision: str,
    confidence: float,
    latency_ms: float,
    reasoning_summary: str = "",
    debate_summary: str = "",
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    content: dict[str, Any] = {
        "question_a": question_a,
        "question_b": question_b,
        "pipeline_used": pipeline_used,
        "decision": decision,
        "latency_ms": latency_ms,
    }
    if reasoning_summary:
        content["reasoning_summary"] = reasoning_summary
    if debate_summary:
        content["debate_summary"] = debate_summary

    tags = ["episodic", pipeline_used, decision]
    return _make_entry(MemoryType.EPISODIC, content, tags, confidence, metadata)


def create_semantic_memory(
    concepts: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    intent_pattern: str,
    semantic_graph: dict[str, Any] | None = None,
    confidence: float = 0.8,
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    content: dict[str, Any] = {
        "concepts": concepts,
        "entities": entities,
        "relations": relations,
        "intent_pattern": intent_pattern,
    }
    if semantic_graph is not None:
        content["semantic_graph"] = semantic_graph

    tags = ["semantic", intent_pattern]
    return _make_entry(MemoryType.SEMANTIC, content, tags, confidence, metadata)


def create_reasoning_memory(
    reasoning_graph: dict[str, Any],
    premises: list[dict[str, Any]],
    evidence_chains: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    confidence_chain: dict[str, Any],
    reasoning_trace: dict[str, Any],
    confidence: float = 0.8,
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    content: dict[str, Any] = {
        "reasoning_graph": reasoning_graph,
        "premises": premises,
        "evidence_chains": evidence_chains,
        "hypotheses": hypotheses,
        "confidence_chain": confidence_chain,
        "reasoning_trace": reasoning_trace,
    }

    tags = ["reasoning"]
    return _make_entry(MemoryType.REASONING, content, tags, confidence, metadata)


def create_debate_memory(
    agent_results: list[dict[str, Any]],
    votes: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    consensus: dict[str, Any],
    disagreements: list[str],
    confidence_distribution: dict[str, Any],
    confidence: float = 0.8,
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    content: dict[str, Any] = {
        "agent_results": agent_results,
        "votes": votes,
        "conflicts": conflicts,
        "consensus": consensus,
        "disagreements": disagreements,
        "confidence_distribution": confidence_distribution,
    }

    tags = ["debate"]
    return _make_entry(MemoryType.DEBATE, content, tags, confidence, metadata)


def create_performance_memory(
    latency_ms: float,
    pipeline_cost: float,
    routing_decision: str,
    memory_hit_rate: float,
    cache_statistics: dict[str, Any] | None = None,
    execution_metrics: dict[str, Any] | None = None,
    confidence: float = 1.0,
    metadata: dict[str, Any] | None = None,
) -> MemoryEntry:
    content: dict[str, Any] = {
        "latency_ms": latency_ms,
        "pipeline_cost": pipeline_cost,
        "routing_decision": routing_decision,
        "memory_hit_rate": memory_hit_rate,
    }
    if cache_statistics is not None:
        content["cache_statistics"] = cache_statistics
    if execution_metrics is not None:
        content["execution_metrics"] = execution_metrics

    tags = ["performance", routing_decision]
    return _make_entry(MemoryType.PERFORMANCE, content, tags, confidence, metadata)
