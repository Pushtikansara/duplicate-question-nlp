"""Lightweight semantic graph — pure dataclass based, no external dependencies.

Maintains a simple graph of typed nodes and typed edges independent of NetworkX.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticNode:
    id: str
    label: str
    node_type: str = "concept"
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticRelation:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticGraph:
    nodes: dict[str, SemanticNode] = field(default_factory=dict)
    edges: list[SemanticRelation] = field(default_factory=list)

    def add_node(self, node: SemanticNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: SemanticRelation) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> SemanticNode | None:
        return self.nodes.get(node_id)

    def get_edges_for(self, node_id: str) -> list[SemanticRelation]:
        return [e for e in self.edges if e.source_id == node_id or e.target_id == node_id]

    def get_outgoing(self, node_id: str) -> list[SemanticRelation]:
        return [e for e in self.edges if e.source_id == node_id]

    def get_incoming(self, node_id: str) -> list[SemanticRelation]:
        return [e for e in self.edges if e.target_id == node_id]

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type, "confidence": n.confidence}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source_id, "target": e.target_id, "type": e.relation_type, "confidence": e.confidence}
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> SemanticGraph:
        graph = cls()
        for nd in data.get("nodes", []):
            graph.add_node(
                SemanticNode(
                    id=nd["id"],
                    label=nd["label"],
                    node_type=nd.get("type", "concept"),
                    confidence=nd.get("confidence", 1.0),
                )
            )
        for ed in data.get("edges", []):
            graph.add_edge(
                SemanticRelation(
                    source_id=ed["source"],
                    target_id=ed["target"],
                    relation_type=ed["type"],
                    confidence=ed.get("confidence", 1.0),
                )
            )
        return graph
