from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceType(Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"


class HypothesisLabel(Enum):
    DUPLICATE = "duplicate"
    NOT_DUPLICATE = "not_duplicate"
    UNCERTAIN = "uncertain"


@dataclass
class Premise:
    id: str
    text: str
    source: str
    category: str
    confidence: float = 1.0
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "category": self.category,
            "confidence": self.confidence,
            "provenance": self.provenance,
        }


@dataclass
class Hypothesis:
    id: str
    label: HypothesisLabel
    text: str
    confidence: float = 0.0
    supporting_premises: list[str] = field(default_factory=list)
    contradicting_premises: list[str] = field(default_factory=list)
    derivation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label.value,
            "text": self.text,
            "confidence": self.confidence,
            "supporting_premises": self.supporting_premises,
            "contradicting_premises": self.contradicting_premises,
            "derivation": self.derivation,
        }


@dataclass
class Evidence:
    id: str
    hypothesis_id: str
    evidence_type: EvidenceType
    text: str
    confidence: float = 1.0
    source_premises: list[str] = field(default_factory=list)
    weight: float = 1.0
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "evidence_type": self.evidence_type.value,
            "text": self.text,
            "confidence": self.confidence,
            "source_premises": self.source_premises,
            "weight": self.weight,
            "provenance": self.provenance,
        }


@dataclass
class ReasoningNode:
    id: str
    node_type: str
    label: str
    confidence: float = 1.0
    children: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "label": self.label,
            "confidence": self.confidence,
            "children": self.children,
            "parents": self.parents,
        }


@dataclass
class ReasoningEdge:
    source_id: str
    target_id: str
    relation: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningGraph:
    nodes: list[ReasoningNode] = field(default_factory=list)
    edges: list[ReasoningEdge] = field(default_factory=list)

    def add_node(self, node: ReasoningNode) -> None:
        self.nodes.append(node)

    def add_edge(self, edge: ReasoningEdge) -> None:
        self.edges.append(edge)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class ReasoningTraceStep:
    step: int
    component: str
    action: str
    detail: str = ""
    confidence: float = 1.0
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "component": self.component,
            "action": self.action,
            "detail": self.detail,
            "confidence": self.confidence,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class ReasoningTrace:
    steps: list[ReasoningTraceStep] = field(default_factory=list)

    def add(self, step: ReasoningTraceStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.steps]


@dataclass
class ProcessingMetadata:
    total_premises: int = 0
    total_hypotheses: int = 0
    total_evidence: int = 0
    total_conflicts: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    processing_time_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)
    components_used: list[str] = field(default_factory=list)


@dataclass
class ConfidenceChain:
    premise_confidence: float = 0.0
    hypothesis_confidence: float = 0.0
    evidence_confidence: float = 0.0
    reasoning_confidence: float = 0.0
    decision_confidence: float = 0.0
    sources: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "premise_confidence": self.premise_confidence,
            "hypothesis_confidence": self.hypothesis_confidence,
            "evidence_confidence": self.evidence_confidence,
            "reasoning_confidence": self.reasoning_confidence,
            "decision_confidence": self.decision_confidence,
            "sources": self.sources,
        }


@dataclass
class ReasoningResult:
    premises: list[Premise] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    supporting_evidence: list[Evidence] = field(default_factory=list)
    contradicting_evidence: list[Evidence] = field(default_factory=list)
    reasoning_graph: ReasoningGraph = field(default_factory=ReasoningGraph)
    reasoning_trace: ReasoningTrace = field(default_factory=ReasoningTrace)
    confidence_chain: ConfidenceChain = field(default_factory=ConfidenceChain)
    decision: str = "uncertain"
    decision_reason: str = ""
    confidence: float = 0.0
    uncertainty: float = 1.0
    processing_metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "premises": [p.to_dict() for p in self.premises],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "reasoning_graph": self.reasoning_graph.to_dict(),
            "reasoning_trace": self.reasoning_trace.to_dict(),
            "confidence_chain": self.confidence_chain.to_dict(),
            "decision": self.decision,
            "decision_reason": self.decision_reason,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "processing_metadata": {
                "total_premises": self.processing_metadata.total_premises,
                "total_hypotheses": self.processing_metadata.total_hypotheses,
                "total_evidence": self.processing_metadata.total_evidence,
                "total_conflicts": self.processing_metadata.total_conflicts,
                "graph_nodes": self.processing_metadata.graph_nodes,
                "graph_edges": self.processing_metadata.graph_edges,
                "processing_time_ms": self.processing_metadata.processing_time_ms,
                "stages": self.processing_metadata.stages,
                "components_used": self.processing_metadata.components_used,
            },
        }
