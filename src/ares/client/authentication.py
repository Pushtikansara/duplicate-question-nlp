from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Authentication:
    def __init__(
        self,
        api_key: str | None = None,
        token: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.token = token

    def get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @property
    def is_authenticated(self) -> bool:
        return bool(self.api_key or self.token)
