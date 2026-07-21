from __future__ import annotations

import re

from ares.plugins.exceptions import PluginCycleError, PluginDependencyError, PluginValidationError
from ares.plugins.metadata import PluginMetadata
from ares.plugins.types import PluginDependency


def validate_metadata(meta: PluginMetadata) -> None:
    """Validate plugin metadata fields."""
    meta.validate()
    if not re.match(r"^\d+\.\d+\.\d+", meta.version):
        raise PluginValidationError(f"Version must be semver: {meta.version!r}")
    for dep in meta.dependencies:
        if not dep.plugin_id or not dep.plugin_id.strip():
            raise PluginValidationError("Dependency plugin_id is required")


def validate_sdk_compatibility(meta: PluginMetadata, current_sdk: str = "0.2.0") -> None:
    """Validate that the plugin's ``compatible_sdk`` spec matches current SDK."""
    spec = meta.compatible_sdk
    if not spec or spec == "*":
        return
    try:
        from packaging.specifiers import SpecifierSet

        spec_set = SpecifierSet(spec)
        if current_sdk not in spec_set:
            raise PluginValidationError(f"Plugin {meta.name!r} requires SDK {spec}, current is {current_sdk}")
    except ImportError:
        pass


def validate_no_duplicate_ids(plugin_id: str, existing_ids: set[str]) -> None:
    """Ensure a plugin ID is not already registered."""
    if plugin_id in existing_ids:
        raise PluginValidationError(f"Duplicate plugin ID: {plugin_id!r}")


def validate_dependencies(
    dependencies: list[PluginDependency],
    available_ids: set[str],
) -> list[str]:
    """Check that all required dependencies are available.

    Returns a list of missing dependency IDs.
    """
    missing: list[str] = []
    for dep in dependencies:
        if not dep.optional and dep.plugin_id not in available_ids:
            missing.append(dep.plugin_id)
    if missing:
        raise PluginDependencyError(f"Missing required dependencies: {', '.join(missing)}")
    return missing


def detect_cycles(
    dependency_map: dict[str, list[str]],
) -> list[list[str]]:
    """Detect cycles in the dependency graph.

    Uses DFS-based cycle detection. Returns a list of cycles (each as a list of IDs).
    """
    visited: set[str] = set()
    path: list[str] = []
    path_set: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        if node in path_set:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for dep in dependency_map.get(node, []):
            dfs(dep)
        path.pop()
        path_set.discard(node)

    for node in dependency_map:
        dfs(node)

    if cycles:
        raise PluginCycleError(f"Cyclic dependencies detected: {cycles}")

    return cycles
