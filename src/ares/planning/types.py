from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class PlanningStrategy(Enum):
    LINEAR = auto()
    TREE = auto()
    DAG = auto()
    GRAPH = auto()
    HIERARCHICAL = auto()
    REACTIVE = auto()
    AUTO = auto()


class PlanNodeStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()
    CANCELLED = auto()
    BLOCKED = auto()


class PlanStatus(Enum):
    DRAFT = auto()
    VALIDATED = auto()
    OPTIMIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    PARTIAL = auto()
    FAILED = auto()
    CANCELLED = auto()


class GoalStatus(Enum):
    PENDING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Goal:
    goal_id: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    parent_goal_id: str | None = None
    sub_goals: list[Goal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_sub_goal(self, goal: Goal) -> None:
        goal.parent_goal_id = self.goal_id
        self.sub_goals.append(goal)


@dataclass
class PlanNode:
    node_id: str
    goal_id: str
    agent_id: str
    action: str
    status: PlanNodeStatus = PlanNodeStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    input: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    error: str | None = None
    cost_estimate: float = 0.0
    latency_estimate_ms: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


@dataclass
class PlanEdge:
    source_id: str
    target_id: str
    condition: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    plan_id: str
    goal_id: str
    status: PlanStatus = PlanStatus.DRAFT
    strategy: PlanningStrategy = PlanningStrategy.LINEAR
    nodes: dict[str, PlanNode] = field(default_factory=dict)
    edges: list[PlanEdge] = field(default_factory=list)
    optimization_stats: dict[str, Any] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def add_node(self, node: PlanNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: PlanEdge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> PlanNode:
        return self.nodes[node_id]

    def get_ready_nodes(self) -> list[PlanNode]:
        completed = {nid for nid, n in self.nodes.items() if n.status == PlanNodeStatus.COMPLETED}
        return [
            n
            for n in self.nodes.values()
            if n.status == PlanNodeStatus.PENDING and all(dep in completed for dep in n.depends_on)
        ]

    def get_execution_order(self) -> list[list[str]]:
        levels: list[list[str]] = []
        remaining = set(self.nodes.keys())
        completed: set[str] = set()
        while remaining:
            level = [nid for nid in remaining if all(dep in completed for dep in self.nodes[nid].depends_on)]
            if not level:
                break
            levels.append(level)
            remaining -= set(level)
            completed |= set(level)
        if remaining:
            levels.append(list(remaining))
        return levels


@dataclass
class PlanResult:
    plan_id: str
    goal_id: str
    status: PlanStatus
    node_results: dict[str, PlanNode]
    total_latency_ms: float = 0.0
    total_cost: float = 0.0
    error: str | None = None
    optimization_summary: dict[str, Any] = field(default_factory=dict)
    execution_timeline: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
