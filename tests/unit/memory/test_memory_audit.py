from __future__ import annotations

import threading

from .conftest import DefaultMemoryAudit


class TestMemoryAudit:
    def test_log_access(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("mem-1", "store", "test_module")
        history = audit.get_history("mem-1")
        assert len(history) == 1
        assert history[0]["action"] == "store"

    def test_get_history(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("mem-1", "store", "mod1")
        audit.log_access("mem-1", "retrieve", "mod2")
        history = audit.get_history("mem-1")
        assert len(history) == 2

    def test_get_history_empty(self) -> None:
        audit = DefaultMemoryAudit()
        assert audit.get_history("no-such") == []

    def test_get_recent_actions(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "store", "mod1")
        audit.log_access("m2", "retrieve", "mod2")
        recent = audit.get_recent_actions()
        assert len(recent) == 2

    def test_get_recent_actions_limit(self) -> None:
        audit = DefaultMemoryAudit()
        for i in range(20):
            audit.log_access(f"m-{i}", "store", "mod")
        recent = audit.get_recent_actions(limit=5)
        assert len(recent) == 5

    def test_audit_entry_fields(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("mem-1", "store", "test_module", details="stored entry")
        history = audit.get_history("mem-1")
        assert len(history) == 1
        entry = history[0]
        assert entry["memory_id"] == "mem-1"
        assert entry["action"] == "store"
        assert entry["module"] == "test_module"
        assert entry["details"] == "stored entry"
        assert "timestamp" in entry

    def test_multiple_accesses(self) -> None:
        audit = DefaultMemoryAudit()
        for _ in range(10):
            audit.log_access("mem-1", "store", "mod")
        assert len(audit.get_history("mem-1")) == 10

    def test_different_action_types(self) -> None:
        audit = DefaultMemoryAudit()
        for action in ["store", "retrieve", "update", "delete", "consolidate"]:
            audit.log_access("mem-1", action, "mod")
        history = audit.get_history("mem-1")
        assert len(history) == 5
        assert {h["action"] for h in history} == {"store", "retrieve", "update", "delete", "consolidate"}

    def test_audit_with_details(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("mem-1", "store", "mod", details="quality=0.9")
        history = audit.get_history("mem-1")
        assert history[0]["details"] == "quality=0.9"

    def test_get_stats(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "store", "mod_a")
        audit.log_access("m1", "store", "mod_a")
        audit.log_access("m2", "retrieve", "mod_b")
        stats = audit.get_stats()
        assert stats["total_entries"] == 3
        assert stats["action_counts"]["store"] == 2
        assert stats["module_counts"]["mod_a"] == 2

    def test_clear_audit(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "store", "mod")
        audit.clear()
        assert audit.get_history("m1") == []
        assert audit.get_recent_actions() == []

    def test_thread_safe_logging(self) -> None:
        audit = DefaultMemoryAudit()
        errors: list[Exception] = []

        def _log() -> None:
            try:
                for _ in range(100):
                    audit.log_access("shared", "store", "mod")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_log) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert len(audit.get_history("shared")) == 400

    def test_audit_ordering(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "first", "mod")
        audit.log_access("m1", "second", "mod")
        history = audit.get_history("m1")
        assert history[0]["action"] == "first"
        assert history[1]["action"] == "second"

    def test_different_modules(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "store", "pipeline")
        audit.log_access("m1", "store", "semantic")
        history = audit.get_history("m1")
        assert len(history) == 2
        assert {h["module"] for h in history} == {"pipeline", "semantic"}

    def test_audit_after_clear_empty(self) -> None:
        audit = DefaultMemoryAudit()
        audit.log_access("m1", "store", "mod")
        audit.clear()
        stats = audit.get_stats()
        assert stats["total_entries"] == 0
