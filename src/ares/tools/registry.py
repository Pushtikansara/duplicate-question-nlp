from __future__ import annotations

import logging
import threading
from typing import Any

from ares.tools.base import Tool
from ares.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from ares.tools.types import ToolMetadata, ToolPermission, ToolSpec, ToolStatus

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tools: dict[str, Tool] = {}
        self._specs: dict[str, ToolSpec] = {}
        self._permissions: dict[str, ToolPermission] = {}
        self._statuses: dict[str, ToolStatus] = {}

    def register(
        self,
        tool: Tool,
        metadata: ToolMetadata | None = None,
        spec: ToolSpec | None = None,
        permission: ToolPermission | None = None,
    ) -> str:
        tool_id = tool.metadata.tool_id
        with self._lock:
            if tool_id in self._tools:
                raise ToolRegistrationError(detail=f"Tool '{tool_id}' is already registered")
            self._tools[tool_id] = tool
            if spec:
                self._specs[tool_id] = spec
            if permission:
                self._permissions[tool_id] = permission
            self._statuses[tool_id] = ToolStatus.AVAILABLE
        logger.info("Registered tool '%s' (%s)", tool_id, tool.metadata.tool_type.name)
        return tool_id

    def unregister(self, tool_id: str) -> None:
        with self._lock:
            self._tools.pop(tool_id, None)
            self._specs.pop(tool_id, None)
            self._permissions.pop(tool_id, None)
            self._statuses.pop(tool_id, None)
        logger.info("Unregistered tool '%s'", tool_id)

    def get(self, tool_id: str) -> Tool:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolNotFoundError(detail=f"Tool '{tool_id}' not found")
        return tool

    def get_spec(self, tool_id: str) -> ToolSpec | None:
        return self._specs.get(tool_id)

    def get_permission(self, tool_id: str) -> ToolPermission | None:
        return self._permissions.get(tool_id)

    def get_status(self, tool_id: str) -> ToolStatus:
        return self._statuses.get(tool_id, ToolStatus.DISABLED)

    def set_status(self, tool_id: str, status: ToolStatus) -> None:
        with self._lock:
            self._statuses[tool_id] = status

    def has(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def list_by_type(self, tool_type: Any) -> list[str]:
        return [tid for tid, t in self._tools.items() if t.metadata.tool_type == tool_type]

    def list_all(self) -> list[str]:
        return list(self._tools.keys())

    def list_available(self) -> list[str]:
        return [tid for tid, s in self._statuses.items() if s == ToolStatus.AVAILABLE]

    def count(self) -> int:
        return len(self._tools)

    def clear(self) -> None:
        with self._lock:
            self._tools.clear()
            self._specs.clear()
            self._permissions.clear()
            self._statuses.clear()
