from __future__ import annotations

from ares.api.exceptions import ARESAPIError


class PlanningError(ARESAPIError):
    status_code = 500
    detail = "Planning error"
    error_code = "PLANNING_ERROR"


class PlanValidationError(PlanningError):
    status_code = 400
    detail = "Plan validation failed"
    error_code = "PLAN_VALIDATION_ERROR"


class PlanExecutionError(PlanningError):
    status_code = 500
    detail = "Plan execution failed"
    error_code = "PLAN_EXECUTION_ERROR"


class PlanNotFoundError(PlanningError):
    status_code = 404
    detail = "Plan not found"
    error_code = "PLAN_NOT_FOUND"


class GoalDecompositionError(PlanningError):
    status_code = 400
    detail = "Goal decomposition failed"
    error_code = "GOAL_DECOMPOSITION_ERROR"


class CircularDependencyError(PlanValidationError):
    status_code = 400
    detail = "Circular dependency detected in plan"
    error_code = "CIRCULAR_DEPENDENCY_ERROR"


class MissingAgentError(PlanValidationError):
    status_code = 400
    detail = "Plan references missing agent"
    error_code = "MISSING_AGENT_ERROR"


class MissingToolError(PlanValidationError):
    status_code = 400
    detail = "Plan references missing tool"
    error_code = "MISSING_TOOL_ERROR"


class InvalidPermissionError(PlanValidationError):
    status_code = 403
    detail = "Plan violates permission model"
    error_code = "INVALID_PERMISSION_ERROR"


class UnreachableNodeError(PlanValidationError):
    status_code = 400
    detail = "Plan contains unreachable nodes"
    error_code = "UNREACHABLE_NODE_ERROR"


class DuplicateNodeError(PlanValidationError):
    status_code = 400
    detail = "Plan contains duplicate nodes"
    error_code = "DUPLICATE_NODE_ERROR"


class DependencyConflictError(PlanValidationError):
    status_code = 400
    detail = "Plan contains dependency conflicts"
    error_code = "DEPENDENCY_CONFLICT_ERROR"


class ReplanningError(PlanningError):
    status_code = 500
    detail = "Replanning failed"
    error_code = "REPLANNING_ERROR"
