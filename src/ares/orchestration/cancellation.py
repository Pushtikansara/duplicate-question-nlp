from __future__ import annotations

import logging

from ares.orchestration.exceptions import RunCancelledError

logger = logging.getLogger(__name__)


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled = False
        self._reason: str | None = None

    def cancel(self, reason: str = "Cancelled by user") -> None:
        self._cancelled = True
        self._reason = reason

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def reason(self) -> str | None:
        return self._reason

    def check(self) -> None:
        if self._cancelled:
            raise RunCancelledError(detail=self._reason or "Run cancelled")


class CancellationManager:
    def __init__(self) -> None:
        self._tokens: dict[str, CancellationToken] = {}

    def create_token(self, run_id: str) -> CancellationToken:
        existing = self._tokens.get(run_id)
        if existing is not None:
            return existing
        token = CancellationToken()
        self._tokens[run_id] = token
        return token

    def cancel(self, run_id: str, reason: str = "Cancelled by user") -> None:
        token = self._tokens.get(run_id)
        if token is not None:
            token.cancel(reason)
            logger.info("Cancelled run '%s': %s", run_id, reason)
        else:
            logger.warning("No cancellation token found for run '%s'", run_id)

    def is_cancelled(self, run_id: str) -> bool:
        token = self._tokens.get(run_id)
        return token is not None and token.is_cancelled

    def get_token(self, run_id: str) -> CancellationToken | None:
        return self._tokens.get(run_id)

    def remove_token(self, run_id: str) -> None:
        self._tokens.pop(run_id, None)

    def clear(self) -> None:
        self._tokens.clear()
