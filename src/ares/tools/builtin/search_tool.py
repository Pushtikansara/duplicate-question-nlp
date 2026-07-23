from __future__ import annotations

import logging
import re
from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    metadata = ToolMetadata(
        tool_id="search",
        name="Search Tool",
        version="1.0",
        description="Search and pattern-match within text data",
        tool_type=ToolType.SEARCH,
        timeout_seconds=10.0,
        requires_permission=True,
    )

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        operation = input.get("operation", "find")
        pattern = input.get("pattern", "")
        text = input.get("text", "")
        data = input.get("data")
        query = input.get("query", "")
        case_sensitive = input.get("case_sensitive", True)

        if not pattern and not query:
            return self.create_output(
                error="No search pattern provided",
                status=ToolStatus.ERROR,
            )

        search_term = pattern or query

        try:
            if operation == "find":
                return self._find_in_text(search_term, text, case_sensitive)
            elif operation == "count":
                return self._count_occurrences(search_term, text, case_sensitive)
            elif operation == "filter":
                return self._filter_data(search_term, data, case_sensitive)
            elif operation == "regex":
                return self._regex_search(pattern, text)
            elif operation == "extract":
                return self._extract_matches(pattern, text)
            elif operation == "replace":
                replacement = input.get("replacement", "")
                return self._replace_text(pattern, replacement, text)
            else:
                return self.create_output(
                    error=f"Unknown operation '{operation}'",
                    status=ToolStatus.ERROR,
                )
        except re.error as e:
            return self.create_output(
                error=f"Invalid regex pattern: {e}",
                status=ToolStatus.ERROR,
            )
        except Exception as e:
            return self.create_output(
                error=f"Search failed: {e}",
                status=ToolStatus.ERROR,
            )

    def _find_in_text(self, pattern: str, text: str, case_sensitive: bool) -> ToolResult:
        if not text:
            return self.create_output(result={"matches": [], "count": 0})
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = list(re.finditer(re.escape(pattern) if not True else pattern, text, flags))
        result_matches = [{"start": m.start(), "end": m.end(), "text": m.group()} for m in matches]
        return self.create_output(result={"pattern": pattern, "matches": result_matches, "count": len(result_matches)})

    def _count_occurrences(self, pattern: str, text: str, case_sensitive: bool) -> ToolResult:
        if not text:
            return self.create_output(result={"pattern": pattern, "count": 0})
        flags = 0 if case_sensitive else re.IGNORECASE
        count = len(list(re.finditer(re.escape(pattern), text, flags)))
        return self.create_output(result={"pattern": pattern, "count": count})

    def _filter_data(self, pattern: str, data: Any, case_sensitive: bool) -> ToolResult:
        if data is None:
            return self.create_output(result={"items": [], "count": 0})
        flags = 0 if case_sensitive else re.IGNORECASE
        if isinstance(data, list):
            matched_items = [
                item for item in data if isinstance(item, str) and re.search(re.escape(pattern), item, flags)
            ]
            return self.create_output(result={"pattern": pattern, "items": matched_items, "count": len(matched_items)})
        if isinstance(data, dict):
            matched_dict = {
                k: v
                for k, v in data.items()
                if re.search(re.escape(pattern), str(k), flags) or re.search(re.escape(pattern), str(v), flags)
            }
            return self.create_output(result={"pattern": pattern, "items": matched_dict, "count": len(matched_dict)})
        return self.create_output(result={"items": [], "count": 0})

    def _regex_search(self, pattern: str, text: str) -> ToolResult:
        if not text:
            return self.create_output(result={"matches": [], "count": 0})
        compiled = re.compile(pattern)
        matches = list(compiled.finditer(text))
        result_matches = [
            {"start": m.start(), "end": m.end(), "text": m.group(), "groups": m.groups()} for m in matches
        ]
        return self.create_output(result={"pattern": pattern, "matches": result_matches, "count": len(result_matches)})

    def _extract_matches(self, pattern: str, text: str) -> ToolResult:
        if not text:
            return self.create_output(result={"extracted": [], "count": 0})
        compiled = re.compile(pattern)
        extracted = compiled.findall(text)
        return self.create_output(result={"pattern": pattern, "extracted": extracted, "count": len(extracted)})

    def _replace_text(self, pattern: str, replacement: str, text: str) -> ToolResult:
        if not text:
            return self.create_output(result={"replaced": "", "count": 0})
        compiled = re.compile(pattern)
        result, count = compiled.subn(replacement, text)
        return self.create_output(result={"pattern": pattern, "replaced": result, "count": count})
