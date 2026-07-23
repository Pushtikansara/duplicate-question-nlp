from __future__ import annotations

import logging
import os
from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class FileTool(Tool):
    metadata = ToolMetadata(
        tool_id="file",
        name="File Tool",
        version="1.0",
        description="Read, write, list, and delete files within allowed paths",
        tool_type=ToolType.FILE,
        timeout_seconds=30.0,
        requires_permission=True,
    )

    def __init__(self, allowed_paths: list[str] | None = None) -> None:
        self._allowed_paths = [os.path.abspath(p) for p in (allowed_paths or [os.getcwd()])]

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        operation = input.get("operation", "read")
        path = input.get("path", "")
        content = input.get("content", "")
        data = input.get("data")

        if not path:
            return self.create_output(
                error="No path provided",
                status=ToolStatus.ERROR,
            )

        abs_path = os.path.abspath(path)
        if not self._is_path_allowed(abs_path):
            return self.create_output(
                error=f"Path '{path}' is not allowed",
                status=ToolStatus.ERROR,
            )

        try:
            if operation == "read":
                return await self._read_file(abs_path)
            elif operation == "write":
                return await self._write_file(abs_path, content)
            elif operation == "list":
                return await self._list_directory(abs_path)
            elif operation == "exists":
                return self._check_exists(abs_path)
            elif operation == "delete":
                return await self._delete_file(abs_path)
            elif operation == "read_json":
                return await self._read_json(abs_path)
            elif operation == "write_json":
                return await self._write_json(abs_path, data)
            else:
                return self.create_output(
                    error=f"Unknown operation '{operation}'",
                    status=ToolStatus.ERROR,
                )
        except PermissionError as e:
            return self.create_output(
                error=f"Permission denied: {e}",
                status=ToolStatus.ERROR,
            )
        except FileNotFoundError as e:
            return self.create_output(
                error=f"File not found: {e}",
                status=ToolStatus.ERROR,
            )
        except Exception as e:
            return self.create_output(
                error=f"File operation failed: {e}",
                status=ToolStatus.ERROR,
            )

    def _is_path_allowed(self, path: str) -> bool:
        return any(path == allowed or path.startswith(allowed + os.sep) for allowed in self._allowed_paths)

    async def _read_file(self, path: str) -> ToolResult:
        with open(path) as f:
            content = f.read()
        return self.create_output(result={"content": content, "path": path, "size": len(content)})

    async def _write_file(self, path: str, content: str) -> ToolResult:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return self.create_output(result={"path": path, "written": len(content)})

    async def _list_directory(self, path: str) -> ToolResult:
        entries = os.listdir(path)
        items = []
        for entry in sorted(entries):
            full = os.path.join(path, entry)
            items.append(
                {
                    "name": entry,
                    "type": "directory" if os.path.isdir(full) else "file",
                    "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                }
            )
        return self.create_output(result={"path": path, "items": items, "count": len(items)})

    def _check_exists(self, path: str) -> ToolResult:
        exists = os.path.exists(path)
        return self.create_output(
            result={"path": path, "exists": exists, "is_file": os.path.isfile(path), "is_dir": os.path.isdir(path)}
        )

    async def _delete_file(self, path: str) -> ToolResult:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        else:
            return self.create_output(error=f"Path not found: {path}", status=ToolStatus.ERROR)
        return self.create_output(result={"path": path, "deleted": True})

    async def _read_json(self, path: str) -> ToolResult:
        import json

        with open(path) as f:
            data = json.load(f)
        return self.create_output(result={"data": data, "path": path})

    async def _write_json(self, path: str, data: Any) -> ToolResult:
        import json

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return self.create_output(result={"path": path, "written": True})
