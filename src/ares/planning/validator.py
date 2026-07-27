from __future__ import annotations

import logging
from collections import deque

from ares.planning.graph import PlanGraph
from ares.planning.types import PlanningStrategy, PlanNode

logger = logging.getLogger(__name__)


class GraphValidator:
    """Validates a PlanGraph for mathematical DAG correctness."""

    def validate(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        errors.extend(self._check_self_loops(graph))
        errors.extend(self._check_duplicate_edges(graph))
        errors.extend(self._check_cycles(graph))
        errors.extend(self._check_missing_nodes(graph))
        errors.extend(self._check_unreachable_nodes(graph))
        errors.extend(self._check_execution_order(graph))
        errors.extend(self._check_strategy_compliance(graph))
        return errors

    def is_dag(self, graph: PlanGraph) -> bool:
        return len(self._find_cycles(graph)) == 0

    def _check_self_loops(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        for edge in graph.plan.edges:
            if edge.source_id == edge.target_id:
                errors.append(f"Self-loop detected: '{edge.source_id}' -> '{edge.target_id}'")
        for nid, node in graph.plan.nodes.items():
            if nid in node.depends_on:
                errors.append(f"Self-loop via depends_on: node '{nid}' depends on itself")
        return errors

    def _check_duplicate_edges(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        seen: set[tuple[str, str, str | None]] = set()
        for edge in graph.plan.edges:
            key = (edge.source_id, edge.target_id, edge.condition)
            if key in seen:
                cond = f" (condition={edge.condition})" if edge.condition else ""
                errors.append(f"Duplicate edge: '{edge.source_id}' -> '{edge.target_id}'{cond}")
            seen.add(key)
        return errors

    def _find_cycles(self, graph: PlanGraph) -> list[list[str]]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in graph.plan.nodes}
        cycles: list[list[str]] = []
        path_stack: list[str] = []

        adjacency: dict[str, list[str]] = {nid: [] for nid in graph.plan.nodes}
        for edge in graph.plan.edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)

        def dfs(node_id: str) -> None:
            color[node_id] = GRAY
            path_stack.append(node_id)
            for neighbor in adjacency.get(node_id, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    cycle_start = path_stack.index(neighbor)
                    cycles.append(path_stack[cycle_start:] + [neighbor])
                elif color[neighbor] == WHITE:
                    dfs(neighbor)
            path_stack.pop()
            color[node_id] = BLACK

        for nid in graph.plan.nodes:
            if color.get(nid) == WHITE:
                dfs(nid)
        return cycles

    def _check_cycles(self, graph: PlanGraph) -> list[str]:
        cycles = self._find_cycles(graph)
        return [f"Cycle detected: {' -> '.join(c)}" for c in cycles]

    def _check_missing_nodes(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        for edge in graph.plan.edges:
            if edge.source_id not in graph.plan.nodes:
                errors.append(f"Edge source '{edge.source_id}' is not a node in the graph")
            if edge.target_id not in graph.plan.nodes:
                errors.append(f"Edge target '{edge.target_id}' is not a node in the graph")
        for node in graph.plan.nodes.values():
            for dep in node.depends_on:
                if dep not in graph.plan.nodes:
                    errors.append(f"Node '{node.node_id}' depends on missing node '{dep}'")
        return errors

    def _check_unreachable_nodes(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        if not graph.plan.nodes:
            return errors
        roots = self._find_roots(graph)
        if not roots:
            errors.append("No root node found (no node without incoming edges)")
            return errors
        reachable: set[str] = set()
        queue: deque[str] = deque(r.node_id for r in roots)
        visited: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            reachable.add(current)
            for edge in graph.plan.edges:
                if edge.source_id == current and edge.target_id not in visited:
                    queue.append(edge.target_id)
        for nid in graph.plan.nodes:
            if nid not in reachable:
                errors.append(f"Node '{nid}' is unreachable (not connected to any root)")
        return errors

    def _find_roots(self, graph: PlanGraph) -> list[PlanNode]:
        has_incoming: set[str] = set()
        for edge in graph.plan.edges:
            has_incoming.add(edge.target_id)
        return [n for n in graph.plan.nodes.values() if n.node_id not in has_incoming]

    def _check_execution_order(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        try:
            order = graph.get_execution_order()
            if not order and graph.plan.nodes:
                errors.append("Execution order is empty but graph has nodes")
            all_ordered = {nid for level in order for nid in level}
            for nid in graph.plan.nodes:
                if nid not in all_ordered:
                    errors.append(f"Node '{nid}' is not included in any execution level")
        except Exception as e:
            errors.append(f"Execution order computation failed: {e}")
        return errors

    def _check_strategy_compliance(self, graph: PlanGraph) -> list[str]:
        errors: list[str] = []
        strategy = graph.plan.strategy
        node_count = len(graph.plan.nodes)
        edge_count = len(graph.plan.edges)
        if strategy == PlanningStrategy.LINEAR and node_count > 0:
            expected_edges = node_count - 1
            if edge_count != expected_edges:
                errors.append(
                    f"LINEAR strategy requires exactly {expected_edges} edges "
                    f"({node_count - 1} for {node_count} nodes), got {edge_count}"
                )
        return errors


class PlanValidator:
    def validate(
        self,
        graph: PlanGraph,
        available_agents: list[str] | None = None,
        available_tools: list[str] | None = None,
    ) -> list[str]:
        errors: list[str] = []

        errors.extend(GraphValidator().validate(graph))
        errors.extend(self._validate_agents(graph, available_agents))
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

    def _validate_agents(self, graph: PlanGraph, available_agents: list[str] | None) -> list[str]:
        if available_agents is None:
            return []
        errors: list[str] = []
        agent_set = set(available_agents)
        for node in graph.plan.nodes.values():
            if node.agent_id not in agent_set:
                errors.append(f"Node '{node.node_id}' references unknown agent '{node.agent_id}'")
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
