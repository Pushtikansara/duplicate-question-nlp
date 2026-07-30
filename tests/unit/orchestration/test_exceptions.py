from __future__ import annotations

from ares.orchestration.exceptions import (
    CacheError,
    InputValidationError,
    MaxRetriesExceededError,
    ModelTimeoutError,
    ModelUnavailableError,
    OrchestrationError,
    PipelineAbortedError,
    PolicyViolationError,
    QueryUnderstandingError,
    RunCancelledError,
    RunTimeoutError,
    StrategyNotFoundError,
    StrategyResolutionError,
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


class TestInputValidationError:
    def test_create(self):
        exc = InputValidationError(detail="Empty question")
        assert exc.status_code == 400
        assert exc.error_code == "INPUT_VALIDATION_ERROR"
        assert exc.detail == "Empty question"
        assert issubclass(InputValidationError, OrchestrationError)


class TestQueryUnderstandingError:
    def test_create(self):
        exc = QueryUnderstandingError(detail="QU failed")
        assert exc.status_code == 500
        assert exc.error_code == "QUERY_UNDERSTANDING_ERROR"
        assert issubclass(QueryUnderstandingError, OrchestrationError)


class TestStrategyResolutionError:
    def test_create(self):
        exc = StrategyResolutionError(detail="Unknown strategy")
        assert exc.status_code == 500
        assert exc.error_code == "STRATEGY_RESOLUTION_ERROR"
        assert issubclass(StrategyResolutionError, OrchestrationError)


class TestModelTimeoutError:
    def test_create(self):
        exc = ModelTimeoutError(detail="Prediction timed out")
        assert exc.status_code == 504
        assert exc.error_code == "MODEL_TIMEOUT_ERROR"
        assert issubclass(ModelTimeoutError, OrchestrationError)


class TestModelUnavailableError:
    def test_create(self):
        exc = ModelUnavailableError(detail="Model not loaded")
        assert exc.status_code == 503
        assert exc.error_code == "MODEL_UNAVAILABLE_ERROR"
        assert issubclass(ModelUnavailableError, OrchestrationError)


class TestCacheError:
    def test_create(self):
        exc = CacheError(detail="Cache unreachable")
        assert exc.status_code == 500
        assert exc.error_code == "CACHE_ERROR"
        assert issubclass(CacheError, OrchestrationError)


class TestPipelineAbortedError:
    def test_create(self):
        exc = PipelineAbortedError(detail="Unrecoverable")
        assert exc.status_code == 500
        assert exc.error_code == "PIPELINE_ABORTED_ERROR"
        assert issubclass(PipelineAbortedError, OrchestrationError)


class TestPredictionExceptionHierarchy:
    def test_all_prediction_errors_under_orchestration_error(self):
        errors = [
            InputValidationError,
            QueryUnderstandingError,
            StrategyResolutionError,
            ModelTimeoutError,
            ModelUnavailableError,
            CacheError,
            PipelineAbortedError,
        ]
        for err in errors:
            assert issubclass(err, OrchestrationError), f"{err.__name__} is not a subclass of OrchestrationError"

    def test_error_codes_unique(self):
        errors = [
            InputValidationError,
            QueryUnderstandingError,
            StrategyResolutionError,
            ModelTimeoutError,
            ModelUnavailableError,
            CacheError,
            PipelineAbortedError,
            StrategyNotFoundError,
            TaskExecutionError,
            TaskDependencyError,
            RunCancelledError,
            RunTimeoutError,
            MaxRetriesExceededError,
            PolicyViolationError,
        ]
        codes = [e.error_code for e in errors]
        assert len(codes) == len(set(codes)), f"Duplicate error codes: {codes}"
