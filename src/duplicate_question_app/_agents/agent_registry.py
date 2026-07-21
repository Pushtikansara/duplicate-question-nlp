from __future__ import annotations

from duplicate_question_app._agents.interfaces import AgentPlugin, CognitiveAgent


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, CognitiveAgent] = {}
        self._plugins: dict[str, AgentPlugin] = {}

    def register(self, agent: CognitiveAgent) -> None:
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> CognitiveAgent | None:
        return self._agents.get(name)

    def get_all(self) -> list[CognitiveAgent]:
        return list(self._agents.values())

    def list_names(self) -> list[str]:
        return list(self._agents.keys())

    def register_plugin(self, plugin: AgentPlugin) -> None:
        self._plugins[plugin.__class__.__name__] = plugin

    def get_plugins(self) -> list[AgentPlugin]:
        return list(self._plugins.values())


_default_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = AgentRegistry()
    return _default_registry
