from __future__ import annotations

from ares.api.exceptions import ARESAPIError


class ToolError(ARESAPIError):
    status_code = 500
    detail = "Tool error"
    error_code = "TOOL_ERROR"


class ToolNotFoundError(ToolError):
    status_code = 404
    detail = "Tool not found"
    error_code = "TOOL_NOT_FOUND"


class ToolExecutionError(ToolError):
    status_code = 500
    detail = "Tool execution failed"
    error_code = "TOOL_EXECUTION_ERROR"


class ToolPermissionError(ToolError):
    status_code = 403
    detail = "Tool permission denied"
    error_code = "TOOL_PERMISSION_DENIED"


class ToolTimeoutError(ToolError):
    status_code = 504
    detail = "Tool execution timed out"
    error_code = "TOOL_TIMEOUT"


class ToolDisabledError(ToolError):
    status_code = 409
    detail = "Tool is disabled"
    error_code = "TOOL_DISABLED"


class ToolRegistrationError(ToolError):
    status_code = 409
    detail = "Tool registration failed"
    error_code = "TOOL_REGISTRATION_ERROR"
