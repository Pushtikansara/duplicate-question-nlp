from __future__ import annotations

import logging
from typing import Any, cast

import httpx

from ares.client.authentication import Authentication
from ares.client.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)
from ares.client.models import (
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    SystemInfoResponse,
    VersionResponse,
)

logger = logging.getLogger(__name__)


class AsyncClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        token: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = Authentication(api_key=api_key, token=token)
        self.timeout = timeout
        self._api_prefix = "/api/v1"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=self.auth.get_headers(),
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        try:
            resp = await client.request(method, f"{self._api_prefix}{path}", json=body)
            if resp.status_code == 401:
                raise AuthenticationError("Invalid or missing credentials")
            elif resp.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif resp.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif resp.status_code >= 400:
                detail = resp.json().get("detail", "") if resp.text else ""
                raise APIError(resp.status_code, detail)
            return cast("dict[str, Any]", resp.json())
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out after {self.timeout}s") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self.base_url}") from e

    async def predict(self, request: PredictionRequest) -> PredictionResponse:
        resp = await self._request(
            "POST",
            "/predict",
            {
                "question1": request.question1,
                "question2": request.question2,
                "model": request.model,
                "threshold": request.threshold,
                "reflect": request.reflect,
            },
        )
        return PredictionResponse.from_dict(resp)

    async def predict_batch(self, pairs: list[tuple[str, str]]) -> BatchPredictionResponse:
        resp = await self._request(
            "POST",
            "/predict/batch",
            {
                "pairs": [{"question1": q1, "question2": q2} for q1, q2 in pairs],
            },
        )
        return BatchPredictionResponse.from_dict(resp)

    async def health(self) -> HealthResponse:
        resp = await self._request("GET", "/health")
        return HealthResponse.from_dict(resp)

    async def version(self) -> VersionResponse:
        resp = await self._request("GET", "/version")
        return VersionResponse.from_dict(resp)

    async def system_info(self) -> SystemInfoResponse:
        resp = await self._request("GET", "/system/info")
        return SystemInfoResponse.from_dict(resp)

    async def search_memory(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return cast(
            "list[dict[str, Any]]", await self._request("POST", "/memory/search", {"query": query, "limit": limit})
        )

    async def list_plugins(self) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", await self._request("GET", "/plugins"))

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
