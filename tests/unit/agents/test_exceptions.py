from __future__ import annotations

from ares.agents.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentPermissionError,
    AgentRegistrationError,
    AgentStateError,
    AgentTimeoutError,
)
from ares.api.exceptions import ARESAPIError


class TestAgentExceptions:
    def test_all_subclass_agent_error(self) -> None:
        exceptions = [
            AgentNotFoundError,
            AgentPermissionError,
            AgentTimeoutError,
            AgentStateError,
            AgentRegistrationError,
            AgentExecutionError,
        ]
        for exc_cls in exceptions:
            assert issubclass(exc_cls, AgentError)

    def test_agent_error_subclass_ares_api_error(self) -> None:
        assert issubclass(AgentError, ARESAPIError)

    def test_not_found_status_code(self) -> None:
        assert AgentNotFoundError.status_code == 404

    def test_permission_denied_status_code(self) -> None:
        assert AgentPermissionError.status_code == 403

    def test_timeout_status_code(self) -> None:
        assert AgentTimeoutError.status_code == 504

    def test_state_error_status_code(self) -> None:
        assert AgentStateError.status_code == 409

    def test_custom_detail(self) -> None:
        err = AgentNotFoundError(detail="Custom message")
        assert err.detail == "Custom message"

    def test_error_code_is_set(self) -> None:
        assert AgentError().error_code == "AGENT_ERROR"
        assert AgentNotFoundError().error_code == "AGENT_NOT_FOUND"
