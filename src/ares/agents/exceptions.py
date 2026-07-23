from __future__ import annotations

from ares.api.exceptions import ARESAPIError


class AgentError(ARESAPIError):
    status_code = 500
    detail = "Agent error"
    error_code = "AGENT_ERROR"


class AgentNotFoundError(AgentError):
    status_code = 404
    detail = "Agent not found"
    error_code = "AGENT_NOT_FOUND"


class AgentPermissionError(AgentError):
    status_code = 403
    detail = "Agent permission denied"
    error_code = "AGENT_PERMISSION_DENIED"


class AgentTimeoutError(AgentError):
    status_code = 504
    detail = "Agent execution timed out"
    error_code = "AGENT_TIMEOUT"


class AgentStateError(AgentError):
    status_code = 409
    detail = "Invalid agent state transition"
    error_code = "AGENT_STATE_ERROR"


class AgentRegistrationError(AgentError):
    status_code = 409
    detail = "Agent registration failed"
    error_code = "AGENT_REGISTRATION_ERROR"


class AgentExecutionError(AgentError):
    status_code = 500
    detail = "Agent execution failed"
    error_code = "AGENT_EXECUTION_ERROR"
