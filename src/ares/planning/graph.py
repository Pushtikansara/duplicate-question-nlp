from __future__ import annotations

import logging
from collections import deque
from typing import Any

from ares.planning.exceptions import CircularDependencyError, DuplicateNodeError
from ares.planning.types import Plan, PlanEdge, PlanNode

logger = logging.getLogger(__name__)


class PlanGraph:
    def __init__(self, plan: Plan | None = None) -> None:
        self._plan = plan or Plan(plan_id="", goal_id="")
        self._adjacency: dict[str, list[tuple[str, str]]] = {}

    @property
    def plan(self) -> Plan:
        return self._plan

    def add_node(self, node: PlanNode) -> None:
        if node.node_id in self._plan.nodes:
            raise DuplicateNodeError(detail=f"Node '{node.node_id}' already exists")
        self._plan.add_node(node)
        self._adjacency.setdefault(node.node_id, [])

    def add_edge(self, edge: PlanEdge) -> None:
        if edge.source_id not in self._plan.nodes:
            raise ValueError(f"Source node '{edge.source_id}' not found")
        if edge.target_id not in self._plan.nodes:
            raise ValueError(f"Target node '{edge.target_id}' not found")
        if self._would_create_cycle(edge.source_id, edge.target_id):
            raise CircularDependencyError(detail=f"Edge '{edge.source_id} -> {edge.target_id}' creates a cycle")
        self._plan.add_edge(edge)
        self._adjacency[edge.source_id].append((edge.target_id, edge.condition or ""))

    def _would_create_cycle(self, source: str, target: str) -> bool:
        visited: set[str] = set()
        queue: deque[str] = deque([target])
        while queue:
            current = queue.popleft()
            if current == source:
                return True
            if current in visited:
                continue
            visited.add(current)
            for neighbor, _ in self._adjacency.get(current, []):
                queue.append(neighbor)
        return False

    def get_node(self, node_id: str) -> PlanNode:
        return self._plan.get_node(node_id)

    def get_ready_nodes(self) -> list[PlanNode]:
        return self._plan.get_ready_nodes()

    def get_execution_order(self) -> list[list[str]]:
        return self._plan.get_execution_order()

    def get_leaves(self) -> list[PlanNode]:
        sources = {e.source_id for e in self._plan.edges}
        return [n for n in self._plan.nodes.values() if n.node_id not in sources]

    def get_roots(self) -> list[PlanNode]:
        sources = {e.source_id for e in self._plan.edges}
        return [n for n in self._plan.nodes.values() if n.node_id not in sources or not self._has_incoming(n.node_id)]

    def _has_incoming(self, node_id: str) -> bool:
        return any(e.target_id == node_id for e in self._plan.edges)

    def get_dependents(self, node_id: str) -> list[PlanNode]:
        dependent_ids = [e.target_id for e in self._plan.edges if e.source_id == node_id]
        return [self._plan.nodes[nid] for nid in dependent_ids if nid in self._plan.nodes]

    def get_dependencies(self, node_id: str) -> list[PlanNode]:
        dep_ids = self._plan.nodes[node_id].depends_on
        return [self._plan.nodes[did] for did in dep_ids if did in self._plan.nodes]

    def get_levels(self) -> list[list[PlanNode]]:
        order = self.get_execution_order()
        return [[self._plan.nodes[nid] for nid in level if nid in self._plan.nodes] for level in order]

    def validate_structure(self) -> list[str]:
        errors: list[str] = []
        for nid, node in self._plan.nodes.items():
            for dep in node.depends_on:
                if dep not in self._plan.nodes:
                    errors.append(f"Node '{nid}' depends on missing node '{dep}'")
        source_ids = {e.source_id for e in self._plan.edges}
        target_ids = {e.target_id for e in self._plan.edges}
        for nid in self._plan.nodes:
            if (
                nid not in source_ids
                and nid not in target_ids
                and len(self._plan.nodes) > 1
                and not any(nid in n.depends_on for n in self._plan.nodes.values() if n.node_id != nid)
                and not any(e.target_id == nid for e in self._plan.edges)
            ):
                errors.append(f"Node '{nid}' is unreachable (no edges)")
        if self._has_duplicate_nodes():
            errors.append("Duplicate nodes detected")
        return errors

    def _has_duplicate_nodes(self) -> bool:
        return len(self._plan.nodes) != len({n.node_id for n in self._plan.nodes.values()})

    def get_complexity(self) -> dict[str, int]:
        return {
            "nodes": len(self._plan.nodes),
            "edges": len(self._plan.edges),
            "levels": len(self.get_execution_order()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self._plan.plan_id,
            "goal_id": self._plan.goal_id,
            "strategy": self._plan.strategy.name,
            "status": self._plan.status.name,
            "nodes": {
                nid: {
                    "node_id": n.node_id,
                    "goal_id": n.goal_id,
                    "agent_id": n.agent_id,
                    "action": n.action,
                    "status": n.status.name,
                    "depends_on": list(n.depends_on),
                    "cost_estimate": n.cost_estimate,
                    "latency_estimate_ms": n.latency_estimate_ms,
                }
                for nid, n in self._plan.nodes.items()
            },
            "edges": [
                {"source_id": e.source_id, "target_id": e.target_id, "condition": e.condition} for e in self._plan.edges
            ],
            "execution_order": self.get_execution_order(),
            "complexity": self.get_complexity(),
        }
