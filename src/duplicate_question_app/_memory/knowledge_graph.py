from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from duplicate_question_app._memory.interfaces import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeNode:
    node_id: str
    label: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class KnowledgeEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: list[KnowledgeEdge] = []
        self._adjacency: dict[str, list[tuple[str, str]]] = {}

    def add_node(self, node: KnowledgeNode) -> None:
        self._nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = []

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self._edges.append(edge)
        if edge.source_id not in self._adjacency:
            self._adjacency[edge.source_id] = []
        if edge.target_id not in self._adjacency:
            self._adjacency[edge.target_id] = []
        self._adjacency[edge.source_id].append((edge.target_id, edge.edge_id))
        self._adjacency[edge.target_id].append((edge.source_id, edge.edge_id))

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[tuple[KnowledgeNode, KnowledgeEdge]]:
        neighbors: list[tuple[KnowledgeNode, KnowledgeEdge]] = []
        adj = self._adjacency.get(node_id, [])
        for neighbor_id, edge_id in adj:
            node = self._nodes.get(neighbor_id)
            edge = next((e for e in self._edges if e.edge_id == edge_id), None)
            if node is not None and edge is not None:
                neighbors.append((node, edge))
        return neighbors

    def traverse(self, start_id: str, max_depth: int = 3) -> list[list[KnowledgeNode]]:
        paths: list[list[KnowledgeNode]] = []

        def dfs(current: str, path: list[KnowledgeNode], depth: int) -> None:
            if depth > max_depth:
                return
            node = self._nodes.get(current)
            if node is None:
                return
            current_path = path + [node]
            paths.append(current_path)
            for neighbor_id, _ in self._adjacency.get(current, []):
                if neighbor_id not in {n.node_id for n in current_path}:
                    dfs(neighbor_id, current_path, depth + 1)

        dfs(start_id, [], 0)
        return paths

    def search_nodes(self, label: str = "", node_type: str = "") -> list[KnowledgeNode]:
        results: list[KnowledgeNode] = []
        for node in self._nodes.values():
            if label and label.lower() not in node.label.lower():
                continue
            if node_type and node.node_type != node_type:
                continue
            results.append(node)
        return results

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {
                nid: {
                    "node_id": n.node_id,
                    "label": n.label,
                    "node_type": n.node_type,
                    "properties": dict(n.properties),
                    "confidence": n.confidence,
                }
                for nid, n in self._nodes.items()
            },
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                    "properties": dict(e.properties),
                }
                for e in self._edges
            ],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> KnowledgeGraph:
        kg = KnowledgeGraph()
        for _nid, ndata in data.get("nodes", {}).items():
            node = KnowledgeNode(
                node_id=ndata["node_id"],
                label=ndata["label"],
                node_type=ndata["node_type"],
                properties=dict(ndata.get("properties", {})),
                confidence=ndata.get("confidence", 1.0),
            )
            kg.add_node(node)
        for edata in data.get("edges", []):
            edge = KnowledgeEdge(
                edge_id=edata["edge_id"],
                source_id=edata["source_id"],
                target_id=edata["target_id"],
                relation=edata["relation"],
                weight=edata.get("weight", 1.0),
                properties=dict(edata.get("properties", {})),
            )
            kg.add_edge(edge)
        return kg

    def build_from_memory(self, entries: list[MemoryEntry]) -> None:
        for entry in entries:
            content = entry.content
            if entry.memory_type == MemoryType.SEMANTIC:
                for concept in content.get("concepts", []):
                    if isinstance(concept, dict):
                        cid = str(concept.get("id", str(uuid.uuid4())))
                        node = KnowledgeNode(
                            node_id=cid,
                            label=str(concept.get("name", concept.get("label", "unknown"))),
                            node_type="concept",
                            properties=concept,
                            confidence=float(concept.get("confidence", entry.confidence)),
                        )
                        self.add_node(node)
                for entity in content.get("entities", []):
                    if isinstance(entity, dict):
                        eid = str(entity.get("id", str(uuid.uuid4())))
                        node = KnowledgeNode(
                            node_id=eid,
                            label=str(entity.get("name", entity.get("label", "unknown"))),
                            node_type="entity",
                            properties=entity,
                            confidence=float(entity.get("confidence", entry.confidence)),
                        )
                        self.add_node(node)
                for relation in content.get("relations", []):
                    if isinstance(relation, dict):
                        edge = KnowledgeEdge(
                            edge_id=relation.get("id", str(uuid.uuid4())),
                            source_id=relation.get("source", ""),
                            target_id=relation.get("target", ""),
                            relation=relation.get("type", "related_to"),
                            weight=relation.get("weight", 1.0),
                            properties=relation,
                        )
                        if edge.source_id and edge.target_id:
                            self.add_edge(edge)
            elif entry.memory_type == MemoryType.EPISODIC:
                qa_id = f"ep_{entry.memory_id}"
                node = KnowledgeNode(
                    node_id=qa_id,
                    label=f"Episodic: {content.get('question_a', '')[:50]}",
                    node_type="episodic",
                    properties={"memory_id": entry.memory_id, "decision": content.get("decision", "")},
                    confidence=entry.confidence,
                )
                self.add_node(node)
            elif entry.memory_type == MemoryType.REASONING:
                rid = f"re_{entry.memory_id}"
                node = KnowledgeNode(
                    node_id=rid,
                    label=f"Reasoning: {entry.memory_id[:8]}",
                    node_type="reasoning",
                    properties={"memory_id": entry.memory_id},
                    confidence=entry.confidence,
                )
                self.add_node(node)
