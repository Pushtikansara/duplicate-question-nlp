from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class GrpcAuthInterceptor:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def authenticate(self, headers: dict[str, str]) -> dict[str, Any] | None:
        token = headers.get("authorization", headers.get("x-api-key", ""))
        if not token:
            return None
        if self._api_key and token == self._api_key:
            return {"sub": "grpc-client", "role": "admin"}
        return {"sub": "anonymous", "role": "reader"}
