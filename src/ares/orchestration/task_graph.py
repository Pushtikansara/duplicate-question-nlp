from __future__ import annotations

import logging
from collections import deque
from typing import Any

from ares.orchestration.exceptions import TaskDependencyError
from ares.orchestration.types import TaskEdge, TaskNode, TaskStatus

logger = logging.getLogger(__name__)


class TaskGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, TaskNode] = {}
        self._edges: list[TaskEdge] = []

    def add_node(self, node: TaskNode) -> str:
        if node.id in self._nodes:
            raise TaskDependencyError(detail=f"Task node '{node.id}' already exists in graph")
        self._nodes[node.id] = node
        return node.id

    def add_edge(self, edge: TaskEdge) -> None:
        if edge.source_id not in self._nodes:
            raise TaskDependencyError(detail=f"Source node '{edge.source_id}' not found in graph")
        if edge.target_id not in self._nodes:
            raise TaskDependencyError(detail=f"Target node '{edge.target_id}' not found in graph")
        if self._would_create_cycle(edge.source_id, edge.target_id):
            raise TaskDependencyError(detail=f"Adding edge '{edge.source_id} -> {edge.target_id}' would create a cycle")
        self._edges.append(edge)

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
            for edge in self._edges:
                if edge.source_id == current:
                    queue.append(edge.target_id)
        return False

    def get_node(self, node_id: str) -> TaskNode:
        node = self._nodes.get(node_id)
        if node is None:
            raise TaskDependencyError(detail=f"Task node '{node_id}' not found in graph")
        return node

    def get_ready_nodes(self) -> list[TaskNode]:
        ready: list[TaskNode] = []
        for node in self._nodes.values():
            if node.status == TaskStatus.PENDING and self._dependencies_met(node.id):
                ready.append(node)
        return ready

    def _dependencies_met(self, node_id: str) -> bool:
        for edge in self._edges:
            if edge.target_id == node_id:
                source_node = self._nodes.get(edge.source_id)
                if source_node and source_node.status != TaskStatus.COMPLETED:
                    return False
        return True

    def topological_sort(self) -> list[list[str]]:
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        adjacency: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        for edge in self._edges:
            if edge.source_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)
                in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
        result: list[list[str]] = []
        visited_count = 0

        while queue:
            batch: list[str] = []
            for _ in range(len(queue)):
                nid = queue.popleft()
                batch.append(nid)
                visited_count += 1
                for neighbor in adjacency.get(nid, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            result.append(batch)

        if visited_count != len(self._nodes):
            raise TaskDependencyError(detail="Graph contains a cycle")
        return result

    def update_node_status(
        self,
        node_id: str,
        status: TaskStatus,
        output: Any = None,
        error: str | None = None,
        processing_time_ms: float = 0.0,
    ) -> None:
        node = self.get_node(node_id)
        updated = TaskNode(
            id=node.id,
            agent_id=node.agent_id,
            status=status,
            depends_on=node.depends_on,
            input=node.input,
            output=output,
            error=error,
            processing_time_ms=processing_time_ms,
            retry_count=node.retry_count,
            metadata=node.metadata,
        )
        self._nodes[node_id] = updated

    def get_dependents(self, node_id: str) -> list[str]:
        return [edge.target_id for edge in self._edges if edge.source_id == node_id]

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def is_complete(self) -> bool:
        return all(
            n.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.CANCELLED) for n in self._nodes.values()
        )

    def reset(self) -> None:
        for nid, node in self._nodes.items():
            self._nodes[nid] = TaskNode(
                id=node.id,
                agent_id=node.agent_id,
                status=TaskStatus.PENDING,
                depends_on=node.depends_on,
                input=node.input,
                metadata=node.metadata,
            )
        self._edges.clear()
