from __future__ import annotations

import pytest

from ares.orchestration.cancellation import CancellationManager, CancellationToken
from ares.orchestration.exceptions import RunCancelledError


class TestCancellationToken:
    def test_create(self):
        token = CancellationToken()
        assert not token.is_cancelled
        assert token.reason is None

    def test_cancel(self):
        token = CancellationToken()
        token.cancel("User requested stop")
        assert token.is_cancelled
        assert token.reason == "User requested stop"

    def test_check_raises(self):
        token = CancellationToken()
        token.cancel("Stopped")
        with pytest.raises(RunCancelledError, match="Stopped"):
            token.check()

    def test_check_not_cancelled(self):
        token = CancellationToken()
        token.check()


class TestCancellationManager:
    def test_create_token(self):
        cm = CancellationManager()
        token = cm.create_token("run_1")
        assert isinstance(token, CancellationToken)
        assert not token.is_cancelled

    def test_cancel(self):
        cm = CancellationManager()
        cm.create_token("run_1")
        cm.cancel("run_1", "Cancelled")
        assert cm.is_cancelled("run_1")

    def test_cancel_unknown(self):
        cm = CancellationManager()
        assert not cm.is_cancelled("unknown")

    def test_get_token(self):
        cm = CancellationManager()
        created = cm.create_token("run_1")
        retrieved = cm.get_token("run_1")
        assert retrieved is created

    def test_get_token_unknown(self):
        cm = CancellationManager()
        assert cm.get_token("unknown") is None

    def test_remove_token(self):
        cm = CancellationManager()
        cm.create_token("run_1")
        cm.remove_token("run_1")
        assert not cm.is_cancelled("run_1")

    def test_clear(self):
        cm = CancellationManager()
        cm.create_token("a")
        cm.create_token("b")
        cm.clear()
        assert cm.get_token("a") is None
        assert cm.get_token("b") is None
