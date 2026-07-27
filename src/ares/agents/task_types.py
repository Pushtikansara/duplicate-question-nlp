from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from ares.agents.types import AgentCapability


class AgentTaskType(Enum):
    VALIDATE_INPUT = auto()
    SELECT_MODEL = auto()
    ENCODE_QUESTIONS = auto()
    PREDICT = auto()
    SEMANTIC_VALIDATE = auto()
    CALIBRATE = auto()
    MEMORY_STORE = auto()
    MEMORY_RETRIEVE = auto()
    REFLECT = auto()
    DECIDE = auto()


TASK_TO_CAPABILITIES: dict[AgentTaskType, set[AgentCapability]] = {
    AgentTaskType.VALIDATE_INPUT: {AgentCapability.MONITORING},
    AgentTaskType.SELECT_MODEL: {AgentCapability.PLANNING},
    AgentTaskType.ENCODE_QUESTIONS: {AgentCapability.SEMANTIC_UNDERSTANDING},
    AgentTaskType.PREDICT: {AgentCapability.PREDICTION, AgentCapability.SEMANTIC_UNDERSTANDING},
    AgentTaskType.SEMANTIC_VALIDATE: {AgentCapability.INTENT_ANALYSIS, AgentCapability.CONFLICT_DETECTION},
    AgentTaskType.CALIBRATE: {AgentCapability.CONFIDENCE_ASSESSMENT},
    AgentTaskType.MEMORY_STORE: {AgentCapability.MEMORY},
    AgentTaskType.MEMORY_RETRIEVE: {AgentCapability.MEMORY},
    AgentTaskType.REFLECT: {AgentCapability.REFLECTION, AgentCapability.CONFIDENCE_ASSESSMENT},
    AgentTaskType.DECIDE: {AgentCapability.REASONING, AgentCapability.CONSENSUS_BUILDING},
}

TASK_DESCRIPTIONS: dict[AgentTaskType, str] = {
    AgentTaskType.VALIDATE_INPUT: "Validate input questions for length and content",
    AgentTaskType.SELECT_MODEL: "Select the appropriate model from registry",
    AgentTaskType.ENCODE_QUESTIONS: "Encode both questions into embeddings",
    AgentTaskType.PREDICT: "Generate duplicate prediction using inference engine",
    AgentTaskType.SEMANTIC_VALIDATE: "Validate prediction for semantic consistency",
    AgentTaskType.CALIBRATE: "Calibrate confidence based on model calibration curve",
    AgentTaskType.MEMORY_STORE: "Store prediction result in memory",
    AgentTaskType.MEMORY_RETRIEVE: "Retrieve similar past predictions from memory",
    AgentTaskType.REFLECT: "Reflect on prediction to assess trust and risk",
    AgentTaskType.DECIDE: "Aggregate all signals into final decision",
}


@dataclass
class AgentTaskSpec:
    task_id: str
    task_type: AgentTaskType
    description: str = ""
    required_capabilities: set[AgentCapability] = field(default_factory=set)
    depends_on: list[str] = field(default_factory=list)
    input_mapping: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    max_retries: int = 2
    agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.description:
            self.description = TASK_DESCRIPTIONS.get(self.task_type, "")
        if not self.required_capabilities:
            self.required_capabilities = TASK_TO_CAPABILITIES.get(self.task_type, set())


@dataclass
class AgentTaskResult:
    task_id: str
    task_type: AgentTaskType
    agent_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    processing_time_ms: float = 0.0
    confidence: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskDecomposition:
    goal_description: str
    tasks: list[AgentTaskSpec] = field(default_factory=list)
    task_results: dict[str, AgentTaskResult] = field(default_factory=dict)
    parallel_groups: list[list[str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: AgentTaskSpec) -> None:
        self.tasks.append(task)

    def add_result(self, result: AgentTaskResult) -> None:
        self.task_results[result.task_id] = result

    def get_result(self, task_type: AgentTaskType) -> AgentTaskResult | None:
        for r in self.task_results.values():
            if r.task_type == task_type:
                return r
        return None

    def all_completed(self) -> bool:
        return all(t.task_id in self.task_results for t in self.tasks)

    def success_rate(self) -> float:
        if not self.task_results:
            return 0.0
        return sum(1 for r in self.task_results.values() if r.success) / len(self.task_results)
