from __future__ import annotations

import pytest

from ares.orchestration.exceptions import MaxRetriesExceededError
from ares.orchestration.retry import RetryManager
from ares.orchestration.types import RunPolicies


class TestRetryManager:
    async def test_execute_success(self):
        rm = RetryManager()
        call_count = 0

        async def succeeds() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await rm.execute_with_retry("task_1", succeeds)
        assert result == "ok"
        assert call_count == 1

    async def test_execute_with_retry_and_recovery(self):
        rm = RetryManager()
        call_count = 0

        async def fails_then_succeeds() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "recovered"

        policies = RunPolicies(retry_on_failure=True, max_retries=5, retry_backoff_base=0.01)
        result = await rm.execute_with_retry("task_2", fails_then_succeeds, policies)
        assert result == "recovered"
        assert call_count == 3

    async def test_execute_exhausts_retries(self):
        rm = RetryManager()
        call_count = 0

        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        policies = RunPolicies(retry_on_failure=True, max_retries=2, retry_backoff_base=0.01)
        with pytest.raises(MaxRetriesExceededError):
            await rm.execute_with_retry("task_3", always_fails, policies)
        assert call_count == 3

    async def test_execute_no_retry(self):
        rm = RetryManager()
        call_count = 0

        async def fails() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("No retry")

        policies = RunPolicies(retry_on_failure=False)
        with pytest.raises(ValueError):
            await rm.execute_with_retry("task_4", fails, policies)
        assert call_count == 1

    def test_get_retry_count(self):
        rm = RetryManager()
        assert rm.get_retry_count("unknown") == 0

    def test_reset(self):
        rm = RetryManager()
        rm._retry_counts["task_1"] = 3
        rm.reset("task_1")
        assert rm.get_retry_count("task_1") == 0

    def test_reset_all(self):
        rm = RetryManager()
        rm._retry_counts["a"] = 1
        rm._retry_counts["b"] = 2
        rm.reset_all()
        assert rm.get_retry_count("a") == 0
        assert rm.get_retry_count("b") == 0
