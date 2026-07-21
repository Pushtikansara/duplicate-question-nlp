from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntegrationConfig:
    enable_perception: bool = True
    enable_routing: bool = True
    enable_memory_read: bool = True
    enable_semantic: bool = True
    enable_reasoning: bool = True
    enable_debate: bool = True
    enable_memory_write: bool = True

    fail_on_perception_error: bool = False
    fail_on_routing_error: bool = False
    fail_on_memory_error: bool = False
    fail_on_semantic_error: bool = False
    fail_on_reasoning_error: bool = False
    fail_on_debate_error: bool = False

    memory_min_confidence: float = 0.3
    memory_read_limit: int = 10
    record_execution_metadata: bool = True
    enable_hooks: bool = True
