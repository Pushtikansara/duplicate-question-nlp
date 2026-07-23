from __future__ import annotations

import logging

from ares.planning.graph import PlanGraph

logger = logging.getLogger(__name__)


class PlanValidator:
    def validate(
        self,
        graph: PlanGraph,
        available_agents: list[str] | None = None,
        available_tools: list[str] | None = None,
    ) -> list[str]:
        errors: list[str] = []

        errors.extend(self._validate_structure(graph))
        errors.extend(self._validate_dependencies(graph))
        errors.extend(self._validate_agents(graph, available_agents))
        errors.extend(self._validate_duplicates(graph))
        errors.extend(self._validate_permissions(graph, available_tools))

        if errors:
            graph.plan.validation_errors = errors
            for err in errors:
                logger.warning("Validation error: %s", err)

        return errors

    def is_valid(
        self,
        graph: PlanGraph,
        available_agents: list[str] | None = None,
        available_tools: list[str] | None = None,
    ) -> bool:
        return len(self.validate(graph, available_agents, available_tools)) == 0

    def _validate_structure(self, graph: PlanGraph) -> list[str]:
        return graph.validate_structure()

    def _validate_dependencies(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        for node in graph.plan.nodes.values():
            if node.depends_on:
                for dep in node.depends_on:
                    if dep not in graph.plan.nodes:
                        errors.append(f"Node '{node.node_id}' depends on missing node '{dep}'")
        return errors

    def _validate_agents(self, graph: PlanGraph, available_agents: list[str] | None) -> list[str]:
        if available_agents is None:
            return []
        errors: list[str] = []
        agent_set = set(available_agents)
        for node in graph.plan.nodes.values():
            if node.agent_id not in agent_set:
                errors.append(f"Node '{node.node_id}' references unknown agent '{node.agent_id}'")
        return errors

    def _validate_duplicates(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        for nid in graph.plan.nodes:
            if nid in seen:
                errors.append(f"Duplicate node ID '{nid}'")
            seen.add(nid)
        edge_keys: set[tuple[str, str]] = set()
        for edge in graph.plan.edges:
            key = (edge.source_id, edge.target_id)
            if key in edge_keys:
                errors.append(f"Duplicate edge '{edge.source_id} -> {edge.target_id}'")
            edge_keys.add(key)
        return errors

    def _validate_permissions(self, graph: PlanGraph, available_tools: list[str] | None) -> list[str]:
        if available_tools is None:
            return []
        errors: list[str] = []
        tool_set = set(available_tools)
        for node in graph.plan.nodes.values():
            node_tools = node.metadata.get("required_tools", [])
            for tool_id in node_tools:
                if tool_id not in tool_set:
                    errors.append(f"Node '{node.node_id}' requires missing tool '{tool_id}'")
        return errors
