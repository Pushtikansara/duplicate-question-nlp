from __future__ import annotations

import logging
from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class PythonTool(Tool):
    metadata = ToolMetadata(
        tool_id="python",
        name="Python Executor",
        version="1.0",
        description="Execute Python code in a restricted environment",
        tool_type=ToolType.PYTHON,
        timeout_seconds=10.0,
        requires_permission=True,
    )

    def __init__(self, restricted_builtins: bool = True) -> None:
        self._restricted_builtins = restricted_builtins

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        code = input.get("code", "")
        globals_dict = input.get("globals", {})
        locals_dict = input.get("locals", {})

        if not code:
            return self.create_output(
                error="No code provided",
                status=ToolStatus.ERROR,
            )

        restricted_builtins_list = [
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "chr",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "hash",
            "hex",
            "id",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
            "True",
            "False",
            "None",
            "Exception",
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "RuntimeError",
            "StopIteration",
            "MemoryError",
        ]

        if self._restricted_builtins:
            safe_builtins: dict[str, Any] = {}
            for name in restricted_builtins_list:
                if hasattr(__builtins__, name):
                    safe_builtins[name] = getattr(__builtins__, name)
                elif isinstance(__builtins__, dict) and name in __builtins__:
                    safe_builtins[name] = __builtins__[name]
        else:
            safe_builtins = dict(__builtins__) if isinstance(__builtins__, dict) else {}

        exec_globals: dict[str, Any] = {
            "__builtins__": safe_builtins,
            "__name__": "__ares_tool__",
            **globals_dict,
        }

        try:
            exec(
                compile(code, "<ares_tool>", "exec"),
                exec_globals,
                locals_dict,
            )
            result = {
                "globals": {
                    k: v
                    for k, v in exec_globals.items()
                    if k not in ("__builtins__", "__name__") and not k.startswith("_")
                },
                "locals": {k: v for k, v in locals_dict.items() if not k.startswith("_")},
            }
            return self.create_output(result=result)
        except Exception as e:
            return self.create_output(
                error=f"Python execution error: {e}",
                status=ToolStatus.ERROR,
            )
