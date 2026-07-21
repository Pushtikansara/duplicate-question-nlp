from __future__ import annotations

from duplicate_question_app._agents.agent import IntentAgent, SemanticAgent
from duplicate_question_app._agents.agent_registry import AgentRegistry, get_agent_registry
from duplicate_question_app._agents.interfaces import AgentPlugin


class TestAgentRegistry:
    def setup_method(self):
        self.registry = AgentRegistry()

    def test_empty_registry(self):
        assert self.registry.get_all() == []
        assert self.registry.list_names() == []

    def test_register_agent(self):
        agent = IntentAgent()
        self.registry.register(agent)
        assert self.registry.get("intent_agent") is agent
        assert "intent_agent" in self.registry.list_names()

    def test_register_multiple(self):
        self.registry.register(IntentAgent())
        self.registry.register(SemanticAgent())
        assert len(self.registry.get_all()) == 2

    def test_unregister(self):
        self.registry.register(IntentAgent())
        self.registry.unregister("intent_agent")
        assert self.registry.get("intent_agent") is None

    def test_get_nonexistent(self):
        assert self.registry.get("nonexistent") is None

    def test_register_plugin(self):
        plugin = _make_dummy_plugin()
        self.registry.register_plugin(plugin)
        assert len(self.registry.get_plugins()) == 1

    def test_get_plugins_empty(self):
        assert self.registry.get_plugins() == []


class _DummyPlugin(AgentPlugin):
    def process(self, rep_a, rep_b, assessment, reasoning_result, agent_results):
        return agent_results


def _make_dummy_plugin() -> AgentPlugin:
    return _DummyPlugin()


class TestGetAgentRegistry:
    def test_singleton(self):
        r1 = get_agent_registry()
        r2 = get_agent_registry()
        assert r1 is r2

    def test_registry_type(self):
        r = get_agent_registry()
        assert isinstance(r, AgentRegistry)
