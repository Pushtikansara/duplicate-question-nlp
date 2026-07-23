from __future__ import annotations

import logging
from typing import Any

from ares.memory import (
    MemoryDomain,
    MemoryError,
    MemoryManager,
    MemoryQuery,
    MemoryTier,
)
from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class MemoryTool(Tool):
    metadata = ToolMetadata(
        tool_id="memory",
        name="Memory Store",
        version="2.0",
        description="Store, retrieve, and manage key-value data in shared memory using the memory integration layer",
        tool_type=ToolType.MEMORY,
        timeout_seconds=10.0,
        requires_permission=True,
    )

    def __init__(self, manager: MemoryManager | None = None) -> None:
        super().__init__()
        self._manager = manager or MemoryManager()

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        operation = input.get("operation", "get")
        key = input.get("key", "")
        value = input.get("value")
        agent_id = input.get("agent_id", "")
        session_id = input.get("session_id", "")
        tier_name = input.get("tier", "WORKING")
        domain_name = input.get("domain", "SEMANTIC")
        tags = input.get("tags", [])
        ttl = input.get("ttl_seconds")
        limit = input.get("limit", 20)

        if operation in ("set", "put", "store") and not key:
            return self.create_output(
                error="No key provided for store operation",
                status=ToolStatus.ERROR,
            )

        try:
            tier = MemoryTier[tier_name.upper()]
        except KeyError:
            return self.create_output(
                error=f"Invalid tier '{tier_name}'. Valid: {[t.name for t in MemoryTier]}",
                status=ToolStatus.ERROR,
            )

        try:
            domain = MemoryDomain[domain_name.upper()]
        except KeyError:
            return self.create_output(
                error=f"Invalid domain '{domain_name}'. Valid: {[d.name for d in MemoryDomain]}",
                status=ToolStatus.ERROR,
            )

        try:
            if operation in ("get", "read", "retrieve"):
                return await self._handle_get(key, agent_id, session_id, tier, limit)
            elif operation in ("set", "put", "store"):
                return await self._handle_store(key, value, tier, domain, ttl, agent_id, session_id, tags)
            elif operation == "delete":
                return await self._handle_delete(key)
            elif operation == "search":
                return await self._handle_search(key, tier, limit)
            elif operation == "stats":
                return await self._handle_stats()
            elif operation == "clear":
                return await self._handle_clear()
            else:
                return self.create_output(
                    error=f"Unknown operation '{operation}'. Valid: get, set, delete, search, stats, clear",
                    status=ToolStatus.ERROR,
                )
        except MemoryError as e:
            return self.create_output(
                error=f"Memory operation failed: {e.detail}",
                status=ToolStatus.ERROR,
            )
        except Exception as e:
            return self.create_output(
                error=f"Memory operation failed: {e}",
                status=ToolStatus.ERROR,
            )

    async def _handle_get(
        self,
        key: str,
        agent_id: str,
        session_id: str,
        tier: MemoryTier,
        limit: int,
    ) -> ToolResult:
        if key:
            q = self._manager.query(MemoryQuery(key=key, tier=tier))
        elif session_id:
            q = self._manager.query(MemoryQuery(session_id=session_id, tier=tier, limit=limit))
        elif agent_id:
            q = self._manager.query(MemoryQuery(agent_id=agent_id, tier=tier, limit=limit))
        else:
            q = self._manager.query(MemoryQuery(tier=tier, limit=limit))

        entries_data = []
        for e in q.entries:
            entries_data.append(
                {
                    "memory_id": e.memory_id,
                    "key": e.key,
                    "value": e.value,
                    "tier": e.tier.name,
                    "domain": e.domain.name,
                    "score": e.score,
                    "timestamp": e.timestamp.isoformat(),
                }
            )
        return self.create_output(
            result={
                "entries": entries_data,
                "count": len(entries_data),
                "total": q.total_count,
                "query_time_ms": q.query_time_ms,
            }
        )

    async def _handle_store(
        self,
        key: str,
        value: Any,
        tier: MemoryTier,
        domain: MemoryDomain,
        ttl: float | None,
        agent_id: str,
        session_id: str,
        tags: list[str],
    ) -> ToolResult:
        entry = self._manager.store(
            key=key,
            value=value,
            tier=tier,
            domain=domain,
            ttl_seconds=ttl,
            agent_id=agent_id,
            session_id=session_id,
            tags=tags,
        )
        return self.create_output(
            result={
                "memory_id": entry.memory_id,
                "key": entry.key,
                "tier": entry.tier.name,
                "domain": entry.domain.name,
                "stored": True,
            }
        )

    async def _handle_delete(self, key: str) -> ToolResult:
        entries = self._manager.search(key)
        if not entries:
            return self.create_output(
                error=f"No entries found for key '{key}'",
                status=ToolStatus.ERROR,
            )
        deleted = 0
        for e in entries:
            if self._manager.delete(e.memory_id):
                deleted += 1
        return self.create_output(result={"key": key, "deleted": deleted})

    async def _handle_search(self, key: str, tier: MemoryTier | None, limit: int) -> ToolResult:
        entries = self._manager.search(key, tier=tier, limit=limit)
        entries_data = [
            {
                "memory_id": e.memory_id,
                "key": e.key,
                "value": e.value,
                "tier": e.tier.name,
                "domain": e.domain.name,
                "score": e.score,
            }
            for e in entries
        ]
        return self.create_output(
            result={
                "query": key,
                "entries": entries_data,
                "count": len(entries_data),
            }
        )

    async def _handle_stats(self) -> ToolResult:
        stats = self._manager.get_stats()
        return self.create_output(
            result={
                "total_entries": stats.total_entries,
                "entries_by_tier": stats.entries_by_tier,
                "entries_by_domain": stats.entries_by_domain,
                "session_count": stats.session_count,
            }
        )

    async def _handle_clear(self) -> ToolResult:
        count = self._manager.clear()
        return self.create_output(result={"cleared": count})
