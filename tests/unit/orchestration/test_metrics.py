from __future__ import annotations

from ares.orchestration.metrics import OrchestrationMetrics


class TestOrchestrationMetrics:
    def test_initial_state(self):
        m = OrchestrationMetrics()
        assert m.total_runs == 0
        assert m.completed_runs == 0
        assert m.failed_runs == 0
        assert m.total_tasks == 0
        assert m.total_processing_time_ms == 0.0

    def test_record_successful_run(self):
        m = OrchestrationMetrics()
        m.record_run(success=True, processing_time_ms=100.0, strategy="sequential")
        assert m.total_runs == 1
        assert m.completed_runs == 1
        assert m.max_processing_time_ms == 100.0
        assert m.min_processing_time_ms == 100.0
        assert m.strategy_counts == {"sequential": 1}

    def test_record_failed_run(self):
        m = OrchestrationMetrics()
        m.record_run(success=False, processing_time_ms=50.0, strategy="parallel")
        assert m.total_runs == 1
        assert m.failed_runs == 1
        assert m.strategy_counts == {"parallel": 1}

    def test_record_cancelled(self):
        m = OrchestrationMetrics()
        m.record_cancelled()
        assert m.total_runs == 1
        assert m.cancelled_runs == 1

    def test_record_timeout(self):
        m = OrchestrationMetrics()
        m.record_timeout(processing_time_ms=200.0)
        assert m.total_runs == 1
        assert m.timed_out_runs == 1
        assert m.total_processing_time_ms == 200.0

    def test_record_task(self):
        m = OrchestrationMetrics()
        m.record_task(task_id="task_1", success=True, processing_time_ms=30.0)
        assert m.total_tasks == 1
        assert m.completed_tasks == 1
        assert "task_1" in m.task_times

    def test_record_task_failed(self):
        m = OrchestrationMetrics()
        m.record_task(task_id="task_1", success=False, processing_time_ms=10.0)
        assert m.total_tasks == 1
        assert m.failed_tasks == 1

    def test_record_task_retried(self):
        m = OrchestrationMetrics()
        m.record_task(task_id="task_1", success=True, processing_time_ms=20.0, retried=True)
        assert m.retried_tasks == 1

    def test_average_processing_time(self):
        m = OrchestrationMetrics()
        m.record_run(success=True, processing_time_ms=100.0)
        m.record_run(success=True, processing_time_ms=200.0)
        assert m.average_processing_time_ms() == 150.0

    def test_average_no_runs(self):
        m = OrchestrationMetrics()
        assert m.average_processing_time_ms() == 0.0

    def test_success_rate(self):
        m = OrchestrationMetrics()
        m.record_run(success=True, processing_time_ms=10.0)
        m.record_run(success=True, processing_time_ms=10.0)
        m.record_run(success=False, processing_time_ms=10.0)
        assert m.success_rate() == 2.0 / 3.0

    def test_success_rate_no_runs(self):
        m = OrchestrationMetrics()
        assert m.success_rate() == 1.0

    def test_min_max_tracking(self):
        m = OrchestrationMetrics()
        m.record_run(success=True, processing_time_ms=300.0)
        m.record_run(success=True, processing_time_ms=100.0)
        m.record_run(success=True, processing_time_ms=200.0)
        assert m.max_processing_time_ms == 300.0
        assert m.min_processing_time_ms == 100.0

    def test_reset(self):
        m = OrchestrationMetrics()
        m.record_run(success=True, processing_time_ms=100.0)
        m.record_task(task_id="t1", success=True, processing_time_ms=50.0)
        m.strategy_counts["seq"] = 1

        m.reset()
        assert m.total_runs == 0
        assert m.total_tasks == 0
        assert m.total_processing_time_ms == 0.0
        assert m.max_processing_time_ms == 0.0
        assert m.min_processing_time_ms == float("inf")
        assert m.strategy_counts == {}
        assert m.task_times == {}
