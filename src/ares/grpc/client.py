from __future__ import annotations

import json
import logging
from typing import Any, cast
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class GrpcClient:
    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
        self._base_url = f"http://{host}:{port}"

    def _request(self, method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}/{method}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, method="POST" if body else "GET")
        req.add_header("Content-Type", "application/json")
        try:
            with urlopen(req, timeout=30) as resp:
                return cast("dict[str, Any]", json.loads(resp.read().decode()))
        except URLError as e:
            logger.error("gRPC request failed: %s", e)
            return {"error": str(e)}
        except Exception as e:
            logger.error("gRPC request error: %s", e)
            return {"error": str(e)}

    def predict(
        self,
        question1: str,
        question2: str,
        model: str | None = None,
        threshold: float | None = None,
        reflect: bool | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "predict",
            {
                "question1": question1,
                "question2": question2,
                "model": model,
                "threshold": threshold,
                "reflect": reflect,
            },
        )

    def predict_batch(self, requests: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request("predict_batch", {"requests": requests})

    def health(self) -> dict[str, Any]:
        return self._request("health")

    def version(self) -> dict[str, Any]:
        return self._request("version")

    def system_info(self) -> dict[str, Any]:
        return self._request("system_info")

    def run_pipeline(
        self,
        question1: str,
        question2: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self._request(
            "pipeline",
            {
                "question1": question1,
                "question2": question2,
                **kwargs,
            },
        )

    def run_reflection(
        self,
        question1: str,
        question2: str,
        prediction: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "reflection",
            {
                "question1": question1,
                "question2": question2,
                "prediction": prediction or {},
            },
        )

    def search_memory(
        self,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "memory_search",
            {
                "query": query,
                "limit": limit,
                "memory_type": memory_type,
            },
        )

    def list_plugins(self) -> dict[str, Any]:
        return self._request("plugins")
