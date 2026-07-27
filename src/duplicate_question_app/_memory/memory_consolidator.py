from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any

from duplicate_question_app._memory.interfaces import (
    MemoryConsolidator,
    MemoryEntry,
    MemoryLineage,
    MemoryStatus,
    MemoryStore,
    MemoryType,
)
from duplicate_question_app._memory.memory_configuration import MemoryConfig

logger = logging.getLogger(__name__)


class DefaultMemoryConsolidator(MemoryConsolidator):
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._config = config or MemoryConfig()

    def consolidate(self, entries: list[MemoryEntry], store: MemoryStore) -> list[str]:
        merged_ids: list[str] = []
        duplicate_groups = self.find_duplicates(entries)

        for group in duplicate_groups:
            if len(group) < 2:
                continue

            merged_entry: MemoryEntry | None = None
            memory_type = group[0].memory_type

            if memory_type == MemoryType.EPISODIC:
                merged_entry = self._merge_episodic(group)
            elif memory_type == MemoryType.SEMANTIC:
                merged_entry = self._merge_semantic(group)
            elif memory_type == MemoryType.REASONING:
                merged_entry = self._merge_reasoning(group)
            else:
                best = max(group, key=lambda e: e.confidence)
                merged_entry = self._merge_episodic([best])

            if merged_entry is not None:
                try:
                    for old_entry in group:
                        store.delete(old_entry.memory_id, soft=True)
                        merged_ids.append(old_entry.memory_id)

                    store.store(merged_entry)
                    merged_ids.append(merged_entry.memory_id)
                    logger.info(
                        "Consolidated %d entries into %s (type=%s)",
                        len(group),
                        merged_entry.memory_id,
                        memory_type.value,
                    )
                except Exception:
                    logger.exception("Failed to consolidate group")

        return merged_ids

    def find_duplicates(self, entries: list[MemoryEntry]) -> list[list[MemoryEntry]]:
        groups: dict[str, list[MemoryEntry]] = {}

        for entry in entries:
            content_hash = self._content_signature(entry)
            groups.setdefault(content_hash, []).append(entry)

        grouped = [g for g in groups.values() if len(g) >= 1]
        grouped.sort(key=len, reverse=True)
        return grouped

    def _content_signature(self, entry: MemoryEntry) -> str:
        key_parts = [entry.memory_type.value]
        if entry.memory_type == MemoryType.EPISODIC:
            key_parts.append(str(entry.content.get("question_a", "")))
            key_parts.append(str(entry.content.get("question_b", "")))
            key_parts.append(str(entry.content.get("decision", "")))
        elif entry.memory_type == MemoryType.SEMANTIC:
            key_parts.append(str(entry.content.get("intent_pattern", "")))
        elif entry.memory_type == MemoryType.REASONING:
            key_parts.append(str(entry.content.get("reasoning_graph", "")))
        elif entry.memory_type == MemoryType.DEBATE:
            consensus = entry.content.get("consensus", {})
            if isinstance(consensus, dict):
                key_parts.append(str(consensus.get("decision", "")))
        elif entry.memory_type == MemoryType.PERFORMANCE:
            key_parts.append(str(entry.content.get("pipeline_cost", "")))
            key_parts.append(str(entry.content.get("routing_decision", "")))

        key_parts.extend(sorted(entry.tags))
        raw = "|".join(key_parts)
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()

    def _merge_episodic(self, group: list[MemoryEntry]) -> MemoryEntry:
        best = max(group, key=lambda e: (e.confidence, e.quality_score))
        all_questions_a = list(dict.fromkeys(e.content.get("question_a", "") for e in group))
        all_questions_b = list(dict.fromkeys(e.content.get("question_b", "") for e in group))
        decisions = [e.content.get("decision", "") for e in group]
        final_decision = max(set(decisions), key=decisions.count)

        all_reasoning = list(
            dict.fromkeys(e.content.get("reasoning_summary", "") for e in group if e.content.get("reasoning_summary"))
        )
        all_debates = list(
            dict.fromkeys(e.content.get("debate_summary", "") for e in group if e.content.get("debate_summary"))
        )

        content: dict[str, Any] = {
            "question_a": all_questions_a[0] if all_questions_a else "",
            "question_b": all_questions_b[0] if all_questions_b else "",
            "pipeline_used": best.content.get("pipeline_used", ""),
            "decision": final_decision,
            "latency_ms": best.content.get("latency_ms", 0.0),
            "merged_from": [e.memory_id for e in group],
            "all_questions_a": all_questions_a,
            "all_questions_b": all_questions_b,
        }
        if all_reasoning:
            content["reasoning_summary"] = "; ".join(all_reasoning)
        if all_debates:
            content["debate_summary"] = "; ".join(all_debates)

        all_parents = []
        for e in group:
            if e.lineage:
                all_parents.extend(e.lineage.parent_ids)
        all_parents = list(dict.fromkeys(all_parents))

        return MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type=MemoryType.EPISODIC,
            version=1,
            timestamp=datetime.now(),
            source_module="_memory",
            quality_score=max(e.quality_score for e in group),
            confidence=sum(e.confidence for e in group) / len(group),
            lineage=MemoryLineage(
                created_by="consolidator",
                created_at=datetime.now(),
                parent_ids=all_parents,
                module_chain=["_memory"],
            ),
            tags=list(dict.fromkeys(t for e in group for t in e.tags)),
            metadata={"consolidated_from": [e.memory_id for e in group]},
            content=content,
            status=MemoryStatus.ACTIVE,
        )

    def _merge_semantic(self, group: list[MemoryEntry]) -> MemoryEntry:
        best = max(group, key=lambda e: e.confidence)
        all_concepts: list[dict] = []
        all_entities: list[dict] = []
        all_relations: list[dict] = []
        seen_concepts: set[str] = set()
        seen_entities: set[str] = set()
        seen_relations: set[str] = set()

        for e in group:
            for c in e.content.get("concepts", []):
                key = str(c.get("id", str(c)))
                if key not in seen_concepts:
                    seen_concepts.add(key)
                    all_concepts.append(c)
            for ent in e.content.get("entities", []):
                key = str(ent.get("id", str(ent)))
                if key not in seen_entities:
                    seen_entities.add(key)
                    all_entities.append(ent)
            for r in e.content.get("relations", []):
                key = str(r.get("id", str(r)))
                if key not in seen_relations:
                    seen_relations.add(key)
                    all_relations.append(r)

        return MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type=MemoryType.SEMANTIC,
            version=1,
            timestamp=datetime.now(),
            source_module="_memory",
            quality_score=max(e.quality_score for e in group),
            confidence=sum(e.confidence for e in group) / len(group),
            lineage=MemoryLineage(
                created_by="consolidator",
                created_at=datetime.now(),
                parent_ids=[],
                module_chain=["_memory"],
            ),
            tags=list(dict.fromkeys(t for e in group for t in e.tags)),
            metadata={"consolidated_from": [e.memory_id for e in group]},
            content={
                "concepts": all_concepts,
                "entities": all_entities,
                "relations": all_relations,
                "intent_pattern": best.content.get("intent_pattern", ""),
            },
            status=MemoryStatus.ACTIVE,
        )

    def _merge_reasoning(self, group: list[MemoryEntry]) -> MemoryEntry:
        best = max(group, key=lambda e: e.confidence)
        all_premises: list[dict] = []
        all_hypotheses: list[dict] = []
        seen_premises: set[str] = set()
        seen_hypotheses: set[str] = set()

        for e in group:
            for p in e.content.get("premises", []):
                key = str(p.get("id", str(p)))
                if key not in seen_premises:
                    seen_premises.add(key)
                    all_premises.append(p)
            for h in e.content.get("hypotheses", []):
                key = str(h.get("id", str(h)))
                if key not in seen_hypotheses:
                    seen_hypotheses.add(key)
                    all_hypotheses.append(h)

        return MemoryEntry(
            memory_id=str(uuid.uuid4()),
            memory_type=MemoryType.REASONING,
            version=1,
            timestamp=datetime.now(),
            source_module="_memory",
            quality_score=max(e.quality_score for e in group),
            confidence=sum(e.confidence for e in group) / len(group),
            lineage=MemoryLineage(
                created_by="consolidator",
                created_at=datetime.now(),
                parent_ids=[],
                module_chain=["_memory"],
            ),
            tags=list(dict.fromkeys(t for e in group for t in e.tags)),
            metadata={"consolidated_from": [e.memory_id for e in group]},
            content={
                "reasoning_graph": best.content.get("reasoning_graph", {}),
                "premises": all_premises,
                "evidence_chains": best.content.get("evidence_chains", []),
                "hypotheses": all_hypotheses,
                "confidence_chain": best.content.get("confidence_chain", {}),
                "reasoning_trace": best.content.get("reasoning_trace", {}),
            },
            status=MemoryStatus.ACTIVE,
        )
