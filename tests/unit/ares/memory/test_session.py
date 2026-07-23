from __future__ import annotations

import time

import pytest

from ares.memory import MemorySession
from ares.memory.exceptions import MemorySessionError


class TestMemorySession:
    def test_create_session(self) -> None:
        session = MemorySession(session_id="my-session")
        assert session.session_id == "my-session"
        assert session.is_active is True
        assert session.age_seconds < 1.0

    def test_random_session_id(self) -> None:
        session = MemorySession()
        assert session.session_id != ""

    def test_working_memory(self, memory_session: MemorySession) -> None:
        memory_session.set_working("key1", "value1")
        assert memory_session.get_working("key1") == "value1"
        assert memory_session.get_working("nonexistent") is None

    def test_get_all_working(self, memory_session: MemorySession) -> None:
        memory_session.set_working("a", 1)
        memory_session.set_working("b", 2)
        all_wm = memory_session.get_all_working()
        assert all_wm == {"a": 1, "b": 2}

    def test_clear_working(self, memory_session: MemorySession) -> None:
        memory_session.set_working("a", 1)
        memory_session.clear_working()
        assert memory_session.get_all_working() == {}

    def test_to_memory_value(self, memory_session: MemorySession) -> None:
        mv = memory_session.to_memory_value("key_x", "val_x")
        assert mv.key == "key_x"
        assert mv.value == "val_x"
        assert mv.session_id == memory_session.session_id

    def test_close(self, memory_session: MemorySession) -> None:
        memory_session.close()
        assert memory_session.is_active is False

    def test_check_active_raises(self, memory_session: MemorySession) -> None:
        memory_session.close()
        with pytest.raises(MemorySessionError):
            memory_session.check_active()

    def test_expired_session(self) -> None:
        session = MemorySession(session_id="expired", ttl_seconds=0.0)
        time.sleep(0.01)
        assert session.is_active is False
