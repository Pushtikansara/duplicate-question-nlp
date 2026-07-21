from __future__ import annotations

import logging
from datetime import datetime

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryValidator

logger = logging.getLogger(__name__)

REQUIRED_CONTENT_FIELDS: dict[str, list[str]] = {
    "episodic": ["question_a", "question_b", "pipeline_used", "decision"],
    "semantic": ["concepts", "entities", "relations", "intent_pattern"],
    "reasoning": [
        "reasoning_graph",
        "premises",
        "evidence_chains",
        "hypotheses",
        "confidence_chain",
        "reasoning_trace",
    ],
    "debate": ["agent_results", "votes", "conflicts", "consensus", "disagreements", "confidence_distribution"],
    "performance": ["latency_ms", "pipeline_cost", "routing_decision", "memory_hit_rate"],
}


class DefaultMemoryValidator(MemoryValidator):
    def validate(self, entry: MemoryEntry) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if not entry.memory_id:
            errors.append("memory_id must not be empty")

        if entry.version < 1:
            errors.append(f"version must be >= 1, got {entry.version}")

        if not isinstance(entry.timestamp, datetime):
            errors.append("timestamp must be a datetime object")

        if not (0.0 <= entry.confidence <= 1.0):
            errors.append(f"confidence must be in [0, 1], got {entry.confidence}")

        if not (0.0 <= entry.quality_score <= 1.0):
            errors.append(f"quality_score must be in [0, 1], got {entry.quality_score}")

        type_name = entry.memory_type.value
        required = REQUIRED_CONTENT_FIELDS.get(type_name, [])
        for field_name in required:
            if field_name not in entry.content:
                errors.append(f"content missing required field '{field_name}' for memory_type '{type_name}'")

        if entry.memory_type.value not in {mt.value for mt in type(entry.memory_type).__members__.values()}:
            valid_types = [mt.value for mt in entry.memory_type.__class__]
            errors.append(f"invalid memory_type '{entry.memory_type}', valid: {valid_types}")

        if not entry.tags:
            errors.append("tags must not be empty")

        if errors:
            logger.warning("Validation failed for memory %s: %s", entry.memory_id, errors)
            return False, errors

        return True, []

    def validate_batch(self, entries: list[MemoryEntry]) -> list[tuple[bool, list[str]]]:
        return [self.validate(e) for e in entries]
