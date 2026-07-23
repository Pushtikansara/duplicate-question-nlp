from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

from ares.orchestration.exceptions import RunTimeoutError
from ares.orchestration.types import RunPolicies

logger = logging.getLogger(__name__)


class TimeoutManager:
    def __init__(self, policies: RunPolicies | None = None) -> None:
        self._policies = policies or RunPolicies()
        self._start_times: dict[str, float] = {}
        self._timeout_flags: dict[str, bool] = {}

    def start_timer(self, task_id: str, timeout_seconds: float | None = None) -> None:
        self._start_times[task_id] = time.time()
        if timeout_seconds is not None:
            self._timeout_flags[task_id] = False

    def stop_timer(self, task_id: str) -> float:
        start = self._start_times.pop(task_id, time.time())
        elapsed = (time.time() - start) * 1000
        self._timeout_flags.pop(task_id, None)
        return elapsed

    def elapsed_seconds(self, task_id: str) -> float:
        start = self._start_times.get(task_id)
        if start is None:
            return 0.0
        return time.time() - start

    def is_timed_out(self, task_id: str, timeout_seconds: float | None = None) -> bool:
        if task_id in self._timeout_flags and self._timeout_flags[task_id]:
            return True
        if timeout_seconds is not None:
            elapsed = self.elapsed_seconds(task_id)
            if elapsed >= timeout_seconds:
                self._timeout_flags[task_id] = True
                return True
        return False

    async def run_with_timeout(
        self,
        task_id: str,
        func: Callable[[], Awaitable[T]],
        timeout_seconds: float | None = None,
        policies: RunPolicies | None = None,
    ) -> T:
        p = policies or self._policies
        timeout = timeout_seconds or p.timeout_seconds

        self.start_timer(task_id, timeout)
        try:
            result: T = await asyncio.wait_for(func(), timeout=timeout)
            self.stop_timer(task_id)
            return result
        except asyncio.TimeoutError:
            self._timeout_flags[task_id] = True
            self.stop_timer(task_id)
            raise RunTimeoutError(detail=f"Task '{task_id}' timed out after {timeout}s") from None

    def reset(self, task_id: str) -> None:
        self._start_times.pop(task_id, None)
        self._timeout_flags.pop(task_id, None)

    def reset_all(self) -> None:
        self._start_times.clear()
        self._timeout_flags.clear()
