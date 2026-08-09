from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from ares.orchestration.exceptions import (
    DuplicateStageError,
    InvalidStageConfigurationError,
    StageDependencyError,
    StageNotFoundError,
)
from ares.orchestration.interfaces import PipelineStage


@dataclass(frozen=True)
class StageDefinition:
    stage: PipelineStage
    enabled: bool = True
    order: int = 0
    depends_on: tuple[str, ...] = field(default_factory=tuple)


class StageRegistry:
    """Registry of pipeline stages.

    Stages are registered by name. Ordering is resolved from explicit order
    values with topological sorting over declared dependencies; stages that
    depend on disabled stages are skipped. Duplicate registrations, missing
    dependencies and dependency cycles are rejected.
    """

    def __init__(self) -> None:
        self._stages: dict[str, StageDefinition] = {}

    def register(
        self,
        stage: PipelineStage,
        *,
        enabled: bool = True,
        order: int = 0,
        depends_on: Iterable[str] = (),
    ) -> None:
        if not isinstance(stage, PipelineStage):
            raise InvalidStageConfigurationError(
                f"Stage '{getattr(stage, 'name', '<unknown>')}' must implement PipelineStage"
            )
        name = stage.name
        if name in self._stages:
            raise DuplicateStageError(f"Stage '{name}' is already registered")
        dependencies = tuple(depends_on)
        if name in dependencies:
            raise StageDependencyError(f"Stage '{name}' cannot depend on itself")
        self._stages[name] = StageDefinition(
            stage=stage,
            enabled=enabled,
            order=order,
            depends_on=dependencies,
        )

    def unregister(self, name: str) -> None:
        if name not in self._stages:
            raise StageNotFoundError(f"Stage '{name}' is not registered")
        del self._stages[name]

    def resolve(self, name: str) -> PipelineStage:
        definition = self._stages.get(name)
        if definition is None:
            raise StageNotFoundError(f"Stage '{name}' is not registered")
        return definition.stage

    def is_registered(self, name: str) -> bool:
        return name in self._stages

    def get_definitions(self) -> dict[str, StageDefinition]:
        return dict(self._stages)

    def get_stage_names(self) -> list[str]:
        return list(self._stages.keys())

    def validate(self) -> None:
        for name, definition in self._stages.items():
            if not definition.enabled:
                continue
            for dependency in definition.depends_on:
                if dependency not in self._stages:
                    raise StageDependencyError(f"Stage '{name}' depends on unknown stage '{dependency}'")
        resolved = {name for name, definition in self._stages.items() if definition.enabled}
        visited: set[str] = set()
        path: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in path:
                cycle = path[path.index(name) :] + [name]
                raise StageDependencyError(f"Circular stage dependency: {' -> '.join(cycle)}")
            path.append(name)
            for dependency in self._stages[name].depends_on:
                if dependency in resolved:
                    visit(dependency)
            path.pop()
            visited.add(name)

        for name in resolved:
            visit(name)

    def ordered_stages(self) -> list[PipelineStage]:
        """Return enabled stages in deterministic execution order.

        A stage is runnable only when every registered dependency is enabled
        (stages depending on disabled or missing stages are excluded).
        Runnable stages are topologically sorted over their declared
        dependencies using Kahn's algorithm; whenever multiple stages are
        available the one with the lowest ``order`` value (then lowest name)
        runs first.
        """
        self.validate()
        runnable: set[str] = set()
        changed = True
        while changed:
            changed = False
            for name, definition in self._stages.items():
                if name in runnable or not definition.enabled:
                    continue
                if set(definition.depends_on) <= runnable:
                    runnable.add(name)
                    changed = True

        dependency_graph: dict[str, set[str]] = {}
        reverse_graph: dict[str, list[str]] = {}
        for name in runnable:
            definition = self._stages[name]
            dependency_graph[name] = {dependency for dependency in definition.depends_on if dependency in runnable}
            reverse_graph.setdefault(name, [])
            for dependency in dependency_graph[name]:
                reverse_graph.setdefault(dependency, []).append(name)

        import heapq

        available: list[tuple[int, str]] = []
        for name in runnable:
            if not dependency_graph[name]:
                heapq.heappush(available, (self._stages[name].order, name))

        ordered: list[PipelineStage] = []
        while available:
            _, name = heapq.heappop(available)
            ordered.append(self._stages[name].stage)
            for dependent in reverse_graph.get(name, []):
                dependency_graph[dependent].discard(name)
                if not dependency_graph[dependent]:
                    heapq.heappush(
                        available,
                        (self._stages[dependent].order, dependent),
                    )
        return ordered
