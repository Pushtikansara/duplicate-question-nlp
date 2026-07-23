from __future__ import annotations

import logging
import time
from typing import Any

from ares.agents.base import Agent
from ares.agents.types import (
    AgentCapability,
    AgentExecutionStatus,
    AgentMetadata,
    AgentOutput,
)
from ares.memory import (
    MemoryDomain,
    MemoryManager,
    MemoryQuery,
    MemoryTier,
)

logger = logging.getLogger(__name__)


class MemoryAgent(Agent):
    metadata = AgentMetadata(
        agent_id="memory",
        name="Memory Agent",
        version="1.0",
        description="Stores and retrieves information using the MemoryManager",
        capabilities=frozenset({AgentCapability.MEMORY}),
        timeout_seconds=30.0,
        max_retries=2,
    )

    def __init__(self, manager: MemoryManager | None = None) -> None:
        super().__init__()
        self._manager = manager or MemoryManager()

    @property
    def manager(self) -> MemoryManager:
        return self._manager

    async def execute(self, input: dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        action = input.get("action", input.get("operation", "store"))

        try:
            if action in ("store", "save", "set", "put"):
                key = input.get("key", "")
                value = input.get("value", input.get("data", {}))
                agent_id = input.get("agent_id", "memory_agent")
                session_id = input.get("session_id", "")
                tags = input.get("tags", [])
                tier_name = input.get("tier", "WORKING")

                if not key:
                    return self.create_output(
                        status=AgentExecutionStatus.FAILURE,
                        error="Key is required for store operation",
                        processing_time_ms=(time.perf_counter() - start) * 1000,
                    )

                tier = getattr(MemoryTier, tier_name.upper(), MemoryTier.WORKING)
                domain = MemoryDomain.SEMANTIC
                if "reflection" in tags or tier_name.upper() == "REFLECTION":
                    domain = MemoryDomain.REFLECTION

                entry = self._manager.store(
                    key=key,
                    value=value,
                    tier=tier,
                    domain=domain,
                    agent_id=agent_id,
                    session_id=session_id,
                    tags=tags,
                )
                elapsed = (time.perf_counter() - start) * 1000

                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={
                        "memory_id": entry.memory_id,
                        "key": entry.key,
                        "tier": entry.tier.name,
                        "domain": entry.domain.name,
                        "stored": True,
                    },
                    processing_time_ms=elapsed,
                )

            elif action in ("get", "read", "retrieve", "search"):
                key = input.get("key", input.get("query", ""))
                limit = input.get("limit", 20)
                tier_name = input.get("tier")

                kwargs: dict[str, Any] = {"limit": limit}
                if tier_name:
                    kwargs["tier"] = getattr(MemoryTier, tier_name.upper(), None)
                if key:
                    entries = self._manager.search(key, **kwargs)
                else:
                    q = MemoryQuery(limit=limit)
                    if tier_name:
                        q.tier = getattr(MemoryTier, tier_name.upper(), None)
                    result = self._manager.query(q)
                    entries = result.entries

                elapsed = (time.perf_counter() - start) * 1000

                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={
                        "entries": [
                            {
                                "memory_id": e.memory_id,
                                "key": e.key,
                                "value": e.value,
                                "tier": e.tier.name,
                                "domain": e.domain.name,
                                "score": e.score,
                                "timestamp": e.timestamp.isoformat(),
                            }
                            for e in entries
                        ],
                        "count": len(entries),
                    },
                    processing_time_ms=elapsed,
                )

            elif action == "stats":
                stats = self._manager.get_stats()
                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={
                        "total_entries": stats.total_entries,
                        "entries_by_tier": stats.entries_by_tier,
                        "entries_by_domain": stats.entries_by_domain,
                        "session_count": stats.session_count,
                    },
                    processing_time_ms=elapsed,
                )

            else:
                elapsed = (time.perf_counter() - start) * 1000
                return self.create_output(
                    status=AgentExecutionStatus.SUCCESS,
                    result={"message": f"Unknown action: {action}"},
                    processing_time_ms=elapsed,
                )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception("MemoryAgent failed")
            return self.create_output(
                status=AgentExecutionStatus.FAILURE,
                error=str(e),
                processing_time_ms=elapsed,
            )
