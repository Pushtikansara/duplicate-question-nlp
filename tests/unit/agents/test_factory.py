from __future__ import annotations

from typing import Any

import pytest

from ares.agents.exceptions import AgentRegistrationError
from ares.agents.factory import AgentFactory, get_agent_types, register_agent_type, unregister_agent_type
from ares.agents.types import AgentMetadata


class TestAgentFactory:
    def test_register_and_create(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("test_agent", concrete_agent_class)
        agent = factory.create("test_agent")
        assert agent is not None
        assert agent.metadata.agent_id == "test_agent"

    def test_create_with_metadata(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("test_agent", concrete_agent_class)
        metadata = AgentMetadata(agent_id="custom", name="Custom", version="2.0")
        agent = factory.create("test_agent", metadata)
        assert agent.metadata.agent_id == "custom"

    def test_register_duplicate_raises(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("test_agent", concrete_agent_class)
        with pytest.raises(AgentRegistrationError):
            factory.register_type("test_agent", concrete_agent_class)

    def test_create_unregistered_raises(self) -> None:
        factory = AgentFactory()
        with pytest.raises(AgentRegistrationError):
            factory.create("nonexistent")

    def test_has_type(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("test_agent", concrete_agent_class)
        assert factory.has_type("test_agent")
        assert not factory.has_type("nonexistent")

    def test_list_types(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        assert factory.list_types() == []
        factory.register_type("a1", concrete_agent_class)
        factory.register_type("a2", concrete_agent_class)
        assert sorted(factory.list_types()) == ["a1", "a2"]

    def test_unregister_type(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("test_agent", concrete_agent_class)
        factory.unregister_type("test_agent")
        assert not factory.has_type("test_agent")

    def test_clear(self, concrete_agent_class: Any) -> None:
        factory = AgentFactory()
        factory.register_type("a1", concrete_agent_class)
        factory.register_type("a2", concrete_agent_class)
        factory.clear()
        assert factory.list_types() == []


class TestModuleLevelFunctions:
    def test_register_and_get_types(self, concrete_agent_class: Any) -> None:
        register_agent_type("mod_agent", concrete_agent_class)
        types = get_agent_types()
        assert "mod_agent" in types
        unregister_agent_type("mod_agent")
        assert "mod_agent" not in get_agent_types()

    def test_register_duplicate_module_level_raises(self, concrete_agent_class: Any) -> None:
        register_agent_type("mod_dup", concrete_agent_class)
        with pytest.raises(AgentRegistrationError):
            register_agent_type("mod_dup", concrete_agent_class)
        unregister_agent_type("mod_dup")
