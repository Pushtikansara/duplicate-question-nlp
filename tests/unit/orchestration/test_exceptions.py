from __future__ import annotations

from ares.orchestration.exceptions import (
    MaxRetriesExceededError,
    OrchestrationError,
    PolicyViolationError,
    RunCancelledError,
    RunTimeoutError,
    StrategyNotFoundError,
    TaskDependencyError,
    TaskExecutionError,
)


class TestOrchestrationExceptions:
    def test_orchestration_error(self):
        exc = OrchestrationError()
        assert exc.status_code == 500
        assert exc.error_code == "ORCHESTRATION_ERROR"

    def test_strategy_not_found(self):
        exc = StrategyNotFoundError(detail="No strategy")
        assert exc.status_code == 404
        assert exc.error_code == "STRATEGY_NOT_FOUND"
        assert exc.detail == "No strategy"

    def test_task_execution_error(self):
        exc = TaskExecutionError(detail="Task failed")
        assert exc.status_code == 500
        assert exc.error_code == "TASK_EXECUTION_ERROR"

    def test_task_dependency_error(self):
        exc = TaskDependencyError(detail="Cycle detected")
        assert exc.status_code == 400
        assert exc.error_code == "TASK_DEPENDENCY_ERROR"

    def test_run_cancelled_error(self):
        exc = RunCancelledError(detail="Cancelled")
        assert exc.status_code == 499
        assert exc.error_code == "RUN_CANCELLED"

    def test_run_timeout_error(self):
        exc = RunTimeoutError(detail="Timed out")
        assert exc.status_code == 504
        assert exc.error_code == "RUN_TIMEOUT"

    def test_max_retries_exceeded(self):
        exc = MaxRetriesExceededError(detail="Too many retries")
        assert exc.status_code == 500
        assert exc.error_code == "MAX_RETRIES_EXCEEDED"

    def test_policy_violation(self):
        exc = PolicyViolationError(detail="Policy violated")
        assert exc.status_code == 400
        assert exc.error_code == "POLICY_VIOLATION"

    def test_hierarchy(self):
        assert issubclass(StrategyNotFoundError, OrchestrationError)
        assert issubclass(TaskExecutionError, OrchestrationError)
        assert issubclass(TaskDependencyError, OrchestrationError)
        assert issubclass(RunCancelledError, OrchestrationError)
        assert issubclass(RunTimeoutError, OrchestrationError)
        assert issubclass(MaxRetriesExceededError, OrchestrationError)
        assert issubclass(PolicyViolationError, OrchestrationError)
