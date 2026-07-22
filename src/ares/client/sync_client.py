from __future__ import annotations

import json
import logging
from typing import Any, cast
from urllib.error import URLError
from urllib.request import Request, urlopen

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


class Client:
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

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self._api_prefix}{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method=method)
        for key, value in self.auth.get_headers().items():
            req.add_header(key, value)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return cast("dict[str, Any]", json.loads(resp.read().decode()))
        except URLError as e:
            if hasattr(e, "code"):
                if e.code == 401:
                    raise AuthenticationError("Invalid or missing credentials") from e
                elif e.code == 404:
                    raise NotFoundError(f"Resource not found: {path}") from e
                elif e.code == 429:
                    raise RateLimitError("Rate limit exceeded") from e
                elif e.code >= 400:
                    detail = ""
                    if hasattr(e, "read"):
                        try:
                            detail = json.loads(e.read().decode()).get("detail", "")
                        except Exception:
                            detail = str(e)
                    raise APIError(e.code, detail) from e
            raise ConnectionError(f"Connection failed: {e}") from e
        except TimeoutError as e:
            raise TimeoutError(f"Request timed out after {self.timeout}s") from e

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        resp = self._request(
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

    def predict_batch(self, pairs: list[tuple[str, str]]) -> BatchPredictionResponse:
        resp = self._request(
            "POST",
            "/predict/batch",
            {
                "pairs": [{"question1": q1, "question2": q2} for q1, q2 in pairs],
            },
        )
        return BatchPredictionResponse.from_dict(resp)

    def health(self) -> HealthResponse:
        resp = self._request("GET", "/health")
        return HealthResponse.from_dict(resp)

    def version(self) -> VersionResponse:
        resp = self._request("GET", "/version")
        return VersionResponse.from_dict(resp)

    def system_info(self) -> SystemInfoResponse:
        resp = self._request("GET", "/system/info")
        return SystemInfoResponse.from_dict(resp)

    def search_memory(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", self._request("POST", "/memory/search", {"query": query, "limit": limit}))

    def list_plugins(self) -> list[dict[str, Any]]:
        return cast("list[dict[str, Any]]", self._request("GET", "/plugins"))
