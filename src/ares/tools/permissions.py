from __future__ import annotations

import logging
import time

from ares.tools.exceptions import ToolDisabledError, ToolPermissionError
from ares.tools.registry import ToolRegistry
from ares.tools.types import ToolStatus

logger = logging.getLogger(__name__)


class ToolPermissionManager:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()
        self._call_counts: dict[str, dict[str, float]] = {}

    def check_permission(
        self,
        tool_id: str,
        agent_id: str = "",
        roles: frozenset[str] | None = None,
    ) -> None:
        status = self._registry.get_status(tool_id)
        if status == ToolStatus.DISABLED:
            raise ToolDisabledError(detail=f"Tool '{tool_id}' is disabled")

        permission = self._registry.get_permission(tool_id)
        if permission is None:
            return

        if permission.allowed_agents and agent_id and agent_id not in permission.allowed_agents:
            raise ToolPermissionError(detail=f"Agent '{agent_id}' is not allowed to use tool '{tool_id}'")

        if permission.allowed_roles and roles and not roles.intersection(permission.allowed_roles):
            raise ToolPermissionError(detail=f"Agent roles {roles} not permitted for tool '{tool_id}'")

        if permission.max_calls_per_minute > 0 and agent_id:
            self._enforce_rate_limit(tool_id, agent_id, permission.max_calls_per_minute)

    def _enforce_rate_limit(
        self,
        tool_id: str,
        agent_id: str,
        max_calls: int,
    ) -> None:
        now = time.time()
        key = f"{tool_id}:{agent_id}"
        if key not in self._call_counts:
            self._call_counts[key] = {}

        window_start = now - 60.0
        recent = [ts for ts in self._call_counts[key].values() if ts > window_start]

        if len(recent) >= max_calls:
            raise ToolPermissionError(detail=f"Rate limit exceeded for tool '{tool_id}' by agent '{agent_id}'")

        call_id = str(len(self._call_counts[key]))
        self._call_counts[key][call_id] = now

    def reset_calls(self) -> None:
        self._call_counts.clear()
