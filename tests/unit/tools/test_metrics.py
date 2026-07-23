from __future__ import annotations

from ares.tools.metrics import ToolMetrics


class TestToolMetrics:
    def test_initial_state(self):
        m = ToolMetrics()
        assert m.total_invocations == 0
        assert m.completed_invocations == 0
        assert m.failed_invocations == 0
        assert m.total_processing_time_ms == 0.0

    def test_record_success(self):
        m = ToolMetrics()
        m.record_invocation("file", True, 100.0)
        assert m.total_invocations == 1
        assert m.completed_invocations == 1
        assert m.tool_counts == {"file": 1}

    def test_record_failure(self):
        m = ToolMetrics()
        m.record_invocation("http", False, 50.0)
        assert m.total_invocations == 1
        assert m.failed_invocations == 1

    def test_record_timeout(self):
        m = ToolMetrics()
        m.record_invocation("search", False, 200.0, timed_out=True)
        assert m.total_invocations == 1
        assert m.timed_out_invocations == 1

    def test_permission_denied(self):
        m = ToolMetrics()
        m.record_permission_denied()
        assert m.permission_denied_count == 1

    def test_average_processing_time(self):
        m = ToolMetrics()
        m.record_invocation("t1", True, 100.0)
        m.record_invocation("t1", True, 200.0)
        assert m.average_processing_time_ms() == 150.0

    def test_average_no_invocations(self):
        m = ToolMetrics()
        assert m.average_processing_time_ms() == 0.0

    def test_success_rate(self):
        m = ToolMetrics()
        m.record_invocation("t1", True, 10.0)
        m.record_invocation("t1", True, 10.0)
        m.record_invocation("t1", False, 10.0)
        assert m.success_rate() == 2.0 / 3.0

    def test_success_rate_no_invocations(self):
        m = ToolMetrics()
        assert m.success_rate() == 1.0

    def test_min_max_tracking(self):
        m = ToolMetrics()
        m.record_invocation("t1", True, 300.0)
        m.record_invocation("t1", True, 100.0)
        m.record_invocation("t1", True, 200.0)
        assert m.max_processing_time_ms == 300.0
        assert m.min_processing_time_ms == 100.0

    def test_reset(self):
        m = ToolMetrics()
        m.record_invocation("t1", True, 100.0)
        m.reset()
        assert m.total_invocations == 0
        assert m.total_processing_time_ms == 0.0
