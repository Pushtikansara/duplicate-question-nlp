from __future__ import annotations

from duplicate_question_app._integration.lifecycle import LifecycleManager, ModuleState


class TestLifecycleManager:
    def test_register_and_get_status(self):
        lm = LifecycleManager()
        lm.register("perception")
        status = lm.get_status("perception")
        assert status is not None
        assert status.name == "perception"
        assert status.state == ModuleState.AVAILABLE

    def test_set_state(self):
        lm = LifecycleManager()
        lm.register("routing")
        lm.set_state("routing", ModuleState.RUNNING)
        assert lm.get_status("routing").state == ModuleState.RUNNING

    def test_set_latency(self):
        lm = LifecycleManager()
        lm.register("semantic")
        lm.set_latency("semantic", 12.5)
        assert lm.get_status("semantic").latency_ms == 12.5

    def test_set_error(self):
        lm = LifecycleManager()
        lm.register("debate")
        lm.set_error("debate", "something went wrong")
        status = lm.get_status("debate")
        assert status.state == ModuleState.FAILED
        assert status.error == "something went wrong"

    def test_get_all_statuses(self):
        lm = LifecycleManager()
        lm.register("a")
        lm.register("b")
        statuses = lm.get_all_statuses()
        assert "a" in statuses
        assert "b" in statuses

    def test_summary(self):
        lm = LifecycleManager()
        lm.register("perception")
        lm.set_latency("perception", 5.0)
        lm.set_state("perception", ModuleState.COMPLETED)
        s = lm.summary()
        assert s["perception"]["state"] == "COMPLETED"
        assert s["perception"]["latency_ms"] == 5.0
