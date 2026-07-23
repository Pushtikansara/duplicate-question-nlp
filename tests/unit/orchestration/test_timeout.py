from __future__ import annotations

import asyncio

import pytest

from ares.orchestration.exceptions import RunTimeoutError
from ares.orchestration.timeout import TimeoutManager


class TestTimeoutManager:
    async def test_run_within_timeout(self):
        tm = TimeoutManager()

        async def quick() -> str:
            await asyncio.sleep(0.01)
            return "done"

        result = await tm.run_with_timeout("task_1", quick, timeout_seconds=5.0)
        assert result == "done"

    async def test_run_exceeds_timeout(self):
        tm = TimeoutManager()

        async def slow() -> str:
            await asyncio.sleep(10)
            return "too late"

        with pytest.raises(RunTimeoutError):
            await tm.run_with_timeout("task_2", slow, timeout_seconds=0.05)

    def test_start_and_stop_timer(self):
        tm = TimeoutManager()
        tm.start_timer("task_3")
        import time

        time.sleep(0.01)
        elapsed = tm.stop_timer("task_3")
        assert elapsed > 0

    def test_elapsed_seconds(self):
        tm = TimeoutManager()
        assert tm.elapsed_seconds("unknown") == 0.0

    def test_is_timed_out(self):
        tm = TimeoutManager()
        tm.start_timer("task_4", timeout_seconds=0.01)
        import time

        time.sleep(0.02)
        assert tm.is_timed_out("task_4", timeout_seconds=0.01)

    def test_is_not_timed_out(self):
        tm = TimeoutManager()
        tm.start_timer("task_5", timeout_seconds=10.0)
        assert not tm.is_timed_out("task_5", timeout_seconds=10.0)

    def test_reset(self):
        tm = TimeoutManager()
        tm.start_timer("task_6")
        tm.reset("task_6")
        assert tm.elapsed_seconds("task_6") == 0.0

    def test_reset_all(self):
        tm = TimeoutManager()
        tm.start_timer("a")
        tm.start_timer("b")
        tm.reset_all()
        assert tm.elapsed_seconds("a") == 0.0
        assert tm.elapsed_seconds("b") == 0.0
