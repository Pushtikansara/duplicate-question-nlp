from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from ares.orchestration.exceptions import MaxRetriesExceededError
from ares.orchestration.types import RunPolicies

logger = logging.getLogger(__name__)


class RetryManager:
    def __init__(self, policies: RunPolicies | None = None) -> None:
        self._policies = policies or RunPolicies()
        self._retry_counts: dict[str, int] = {}

    async def execute_with_retry(
        self,
        task_id: str,
        func: Callable[[], Any],
        policies: RunPolicies | None = None,
    ) -> Any:
        p = policies or self._policies
        max_retries = p.max_retries if p.retry_on_failure else 0
        base_backoff = p.retry_backoff_base

        for attempt in range(max_retries + 1):
            try:
                result = await func()
                self._retry_counts[task_id] = attempt
                return result
            except Exception as e:
                self._retry_counts[task_id] = attempt + 1
                if attempt < max_retries:
                    backoff = base_backoff * (2**attempt)
                    logger.warning(
                        "Task '%s' attempt %d/%d failed: %s. Retrying in %.2fs",
                        task_id,
                        attempt + 1,
                        max_retries + 1,
                        e,
                        backoff,
                    )
                    time.sleep(backoff)
                else:
                    if max_retries == 0:
                        raise
                    raise MaxRetriesExceededError(
                        detail=f"Task '{task_id}' failed after {max_retries + 1} attempts: {e}"
                    ) from e

    def get_retry_count(self, task_id: str) -> int:
        return self._retry_counts.get(task_id, 0)

    def reset(self, task_id: str) -> None:
        self._retry_counts.pop(task_id, None)

    def reset_all(self) -> None:
        self._retry_counts.clear()
