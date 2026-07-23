from __future__ import annotations

import logging
from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class PluginTool(Tool):
    metadata = ToolMetadata(
        tool_id="plugin",
        name="Plugin Manager",
        version="1.0",
        description="List, load, unload, and query plugins",
        tool_type=ToolType.PLUGIN,
        timeout_seconds=10.0,
        requires_permission=True,
    )

    _loaded_plugins: dict[str, dict[str, Any]] = {}

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        operation = input.get("operation", "list")
        plugin_id = input.get("plugin_id", "")
        plugin_path = input.get("plugin_path", "")
        plugin_config = input.get("config", {})

        try:
            if operation == "list":
                return self._list_plugins()
            elif operation == "load":
                return await self._load_plugin(plugin_id, plugin_path, plugin_config)
            elif operation == "unload":
                return await self._unload_plugin(plugin_id)
            elif operation == "status":
                return self._plugin_status(plugin_id)
            elif operation == "reload":
                return await self._reload_plugin(plugin_id, plugin_path, plugin_config)
            else:
                return self.create_output(
                    error=f"Unknown operation '{operation}'",
                    status=ToolStatus.ERROR,
                )
        except Exception as e:
            return self.create_output(
                error=f"Plugin operation failed: {e}",
                status=ToolStatus.ERROR,
            )

    def _list_plugins(self) -> ToolResult:
        plugins = [
            {
                "id": pid,
                "status": info.get("status", "unknown"),
                "name": info.get("name", pid),
            }
            for pid, info in self._loaded_plugins.items()
        ]
        return self.create_output(result={"plugins": plugins, "count": len(plugins)})

    async def _load_plugin(self, plugin_id: str, plugin_path: str, config: dict[str, Any]) -> ToolResult:
        if not plugin_id:
            return self.create_output(error="No plugin_id provided", status=ToolStatus.ERROR)
        if plugin_id in self._loaded_plugins:
            return self.create_output(error=f"Plugin '{plugin_id}' already loaded", status=ToolStatus.ERROR)

        self._loaded_plugins[plugin_id] = {
            "name": plugin_id,
            "status": "loaded",
            "path": plugin_path or f"plugin://{plugin_id}",
            "config": config,
        }
        return self.create_output(result={"plugin_id": plugin_id, "loaded": True})

    async def _unload_plugin(self, plugin_id: str) -> ToolResult:
        if plugin_id not in self._loaded_plugins:
            return self.create_output(error=f"Plugin '{plugin_id}' not found", status=ToolStatus.ERROR)
        del self._loaded_plugins[plugin_id]
        return self.create_output(result={"plugin_id": plugin_id, "unloaded": True})

    def _plugin_status(self, plugin_id: str) -> ToolResult:
        if plugin_id not in self._loaded_plugins:
            return self.create_output(error=f"Plugin '{plugin_id}' not found", status=ToolStatus.ERROR)
        info = self._loaded_plugins[plugin_id]
        return self.create_output(result={"plugin_id": plugin_id, "status": info})

    async def _reload_plugin(self, plugin_id: str, plugin_path: str, config: dict[str, Any]) -> ToolResult:
        await self._unload_plugin(plugin_id)
        return await self._load_plugin(plugin_id, plugin_path, config)
