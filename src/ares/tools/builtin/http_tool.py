from __future__ import annotations

import logging
from typing import Any

from ares.tools.base import Tool
from ares.tools.types import ToolMetadata, ToolResult, ToolStatus, ToolType

logger = logging.getLogger(__name__)


class HTTPTool(Tool):
    metadata = ToolMetadata(
        tool_id="http",
        name="HTTP Client",
        version="1.0",
        description="Make HTTP GET and POST requests",
        tool_type=ToolType.HTTP,
        timeout_seconds=30.0,
        requires_permission=True,
    )

    def __init__(self, allowed_domains: list[str] | None = None) -> None:
        self._allowed_domains = allowed_domains

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        method = input.get("method", "GET").upper()
        url = input.get("url", "")
        headers = input.get("headers", {})
        params = input.get("params")
        body = input.get("body")
        json_data = input.get("json")
        timeout = input.get("timeout", 10.0)

        if not url:
            return self.create_output(
                error="No URL provided",
                status=ToolStatus.ERROR,
            )

        try:
            import httpx

            if self._allowed_domains:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                allowed = False
                for allowed_domain in self._allowed_domains:
                    if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                        allowed = True
                        break
                if not allowed:
                    return self.create_output(
                        error=f"Domain '{domain}' is not allowed",
                        status=ToolStatus.ERROR,
                    )

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    if json_data is not None:
                        response = await client.post(url, headers=headers, json=json_data)
                    elif body is not None:
                        response = await client.post(url, headers=headers, content=body)
                    else:
                        response = await client.post(url, headers=headers)
                elif method == "PUT":
                    if json_data is not None:
                        response = await client.put(url, headers=headers, json=json_data)
                    elif body is not None:
                        response = await client.put(url, headers=headers, content=body)
                    else:
                        response = await client.put(url, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                elif method == "HEAD":
                    response = await client.head(url, headers=headers)
                else:
                    return self.create_output(
                        error=f"Unsupported HTTP method '{method}'",
                        status=ToolStatus.ERROR,
                    )

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    result_body = response.json()
                except Exception:
                    result_body = response.text
            else:
                result_body = response.text

            return self.create_output(
                result={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": result_body,
                    "url": str(response.url),
                    "elapsed_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, "elapsed") else 0,
                }
            )

        except ImportError:
            return self.create_output(
                error="httpx library is not available. Install with: pip install httpx",
                status=ToolStatus.ERROR,
            )
        except Exception as e:
            return self.create_output(
                error=f"HTTP request failed: {e}",
                status=ToolStatus.ERROR,
            )
