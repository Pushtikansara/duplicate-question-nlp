from __future__ import annotations

import pytest

from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import (
    DuplicateStageError,
    InvalidStageConfigurationError,
    StageDependencyError,
)
from ares.orchestration.interfaces import PipelineStage
from ares.orchestration.metadata import OrchestrationMetadata
from ares.orchestration.stage_registry import StageDefinition, StageRegistry


class RecordingStage(PipelineStage):
    def __init__(self, name: str) -> None:
        self._name = name
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        self.calls.append(self._name)


def _input() -> PredictionInput:
    return PredictionInput(question1="a", question2="b")


def _state() -> PipelineState:
    return PipelineState()


def _metadata() -> OrchestrationMetadata:
    return OrchestrationMetadata()


def _stages(names: list[str]) -> list[RecordingStage]:
    return [RecordingStage(name) for name in names]


class TestRegister:
    def test_register_and_resolve(self) -> None:
        registry = StageRegistry()
        stage = RecordingStage("A")
        registry.register(stage, order=1)
        assert registry.is_registered("A")
        assert registry.resolve("A") is stage

    def test_duplicate_registration_raises(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"))
        with pytest.raises(DuplicateStageError):
            registry.register(RecordingStage("A"))

    def test_non_pipeline_stage_rejected(self) -> None:
        registry = StageRegistry()
        with pytest.raises(InvalidStageConfigurationError):

            class NotAStage:
                pass

            registry.register(NotAStage())  # type: ignore[arg-type]

    def test_self_dependency_rejected(self) -> None:
        registry = StageRegistry()
        with pytest.raises(StageDependencyError):
            registry.register(RecordingStage("A"), depends_on=["A"])

    def test_unregister(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"))
        registry.unregister("A")
        assert not registry.is_registered("A")


class TestOrdering:
    def test_explicit_order_respected(self) -> None:
        registry = StageRegistry()
        a, b, c = _stages(["A", "B", "C"])
        registry.register(c, order=3)
        registry.register(a, order=1)
        registry.register(b, order=2)
        assert [s.name for s in registry.ordered_stages()] == ["A", "B", "C"]

    def test_dependencies_override_order(self) -> None:
        registry = StageRegistry()
        a, b, c = _stages(["A", "B", "C"])
        registry.register(a, order=1)
        registry.register(b, order=2, depends_on=["C"])
        registry.register(c, order=3)
        assert [s.name for s in registry.ordered_stages()] == ["A", "C", "B"]

    def test_disabled_stage_excluded_and_dependents_reevaluated(self) -> None:
        registry = StageRegistry()
        a, b, c = _stages(["A", "B", "C"])
        registry.register(a, order=1, enabled=False)
        registry.register(b, order=2, depends_on=["A"])
        registry.register(c, order=3)
        assert [s.name for s in registry.ordered_stages()] == ["C"]

    def test_unknown_dependency_raises(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"), depends_on=["MISSING"])
        with pytest.raises(StageDependencyError):
            registry.ordered_stages()

    def test_cycle_raises(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"), depends_on=["B"])
        registry.register(RecordingStage("B"), depends_on=["A"])
        with pytest.raises(StageDependencyError):
            registry.ordered_stages()

    def test_independent_stages_ordered_by_name(self) -> None:
        registry = StageRegistry()
        z, a = _stages(["Z", "A"])
        registry.register(z)
        registry.register(a)
        assert [s.name for s in registry.ordered_stages()] == ["A", "Z"]


class TestDefinition:
    def test_stage_definition_carries_config(self) -> None:
        stage = RecordingStage("A")
        definition = StageDefinition(stage=stage, enabled=True, order=5, depends_on=("B",))
        assert definition.stage is stage
        assert definition.enabled is True
        assert definition.order == 5
        assert definition.depends_on == ("B",)

    def test_validate_passes_for_healthy_registry(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"))
        registry.register(RecordingStage("B"), depends_on=["A"])
        registry.validate()  # should not raise

    def test_get_definitions_and_names(self) -> None:
        registry = StageRegistry()
        registry.register(RecordingStage("A"))
        registry.register(RecordingStage("B"))
        assert set(registry.get_definitions()) == {"A", "B"}
        assert registry.get_stage_names() == ["A", "B"]
