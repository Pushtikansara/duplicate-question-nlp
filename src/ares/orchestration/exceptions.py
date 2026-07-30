from __future__ import annotations

from ares.api.exceptions import ARESAPIError


class OrchestrationError(ARESAPIError):
    status_code = 500
    detail = "Orchestration error"
    error_code = "ORCHESTRATION_ERROR"


class StrategyNotFoundError(OrchestrationError):
    status_code = 404
    detail = "Orchestration strategy not found"
    error_code = "STRATEGY_NOT_FOUND"


class TaskExecutionError(OrchestrationError):
    status_code = 500
    detail = "Task execution failed"
    error_code = "TASK_EXECUTION_ERROR"


class TaskDependencyError(OrchestrationError):
    status_code = 400
    detail = "Circular or missing task dependency"
    error_code = "TASK_DEPENDENCY_ERROR"


class RunCancelledError(OrchestrationError):
    status_code = 499
    detail = "Orchestration run was cancelled"
    error_code = "RUN_CANCELLED"


class RunTimeoutError(OrchestrationError):
    status_code = 504
    detail = "Orchestration run timed out"
    error_code = "RUN_TIMEOUT"


class MaxRetriesExceededError(OrchestrationError):
    status_code = 500
    detail = "Maximum retries exceeded"
    error_code = "MAX_RETRIES_EXCEEDED"


class PolicyViolationError(OrchestrationError):
    status_code = 400
    detail = "Run policy violation"
    error_code = "POLICY_VIOLATION"


class InputValidationError(OrchestrationError):
    status_code = 400
    detail = "Invalid prediction input"
    error_code = "INPUT_VALIDATION_ERROR"


class QueryUnderstandingError(OrchestrationError):
    status_code = 500
    detail = "Query understanding pipeline failed"
    error_code = "QUERY_UNDERSTANDING_ERROR"


class StrategyResolutionError(OrchestrationError):
    status_code = 500
    detail = "Strategy resolution failed"
    error_code = "STRATEGY_RESOLUTION_ERROR"


class ModelTimeoutError(OrchestrationError):
    status_code = 504
    detail = "Prediction model timed out"
    error_code = "MODEL_TIMEOUT_ERROR"


class ModelUnavailableError(OrchestrationError):
    status_code = 503
    detail = "Prediction model is unavailable"
    error_code = "MODEL_UNAVAILABLE_ERROR"


class CacheError(OrchestrationError):
    status_code = 500
    detail = "Cache operation failed"
    error_code = "CACHE_ERROR"


class PipelineAbortedError(OrchestrationError):
    status_code = 500
    detail = "Pipeline aborted due to unrecoverable error"
    error_code = "PIPELINE_ABORTED_ERROR"
