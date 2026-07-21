from __future__ import annotations

from collections import defaultdict, deque

from ares.plugins.exceptions import PluginCycleError, PluginDependencyError
from ares.plugins.metadata import PluginMetadata


def build_dependency_graph(
    plugins: dict[str, PluginMetadata],
) -> dict[str, list[str]]:
    """Build a directed adjacency list of plugin dependencies."""
    graph: dict[str, list[str]] = {}
    for pid, meta in plugins.items():
        graph[pid] = [d.plugin_id for d in meta.dependencies if not d.optional]
    return graph


def topological_sort(
    graph: dict[str, list[str]],
) -> list[str]:
    """Topologically sort plugins by dependencies.

    Uses Kahn's algorithm. Raises PluginCycleError if a cycle exists.
    """
    in_degree: dict[str, int] = {}
    dependents: dict[str, list[str]] = defaultdict(list)

    for node, deps in graph.items():
        in_degree.setdefault(node, 0)
        for dep in deps:
            in_degree.setdefault(dep, 0)
            dependents[dep].append(node)

    for node, deps in graph.items():
        in_degree[node] = len(deps)

    queue: deque[str] = deque()
    for node, deg in in_degree.items():
        if deg == 0 and node in graph:
            queue.append(node)

    sorted_list: list[str] = []
    while queue:
        node = queue.popleft()
        sorted_list.append(node)
        for dependent in dependents.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_list) != len(graph):
        raise PluginCycleError("Circular dependency detected in plugin graph")

    return sorted_list


def resolve_load_order(
    plugins: dict[str, PluginMetadata],
) -> list[str]:
    """Return plugin IDs in load order (dependencies first).

    Validates that all required dependencies are present before sorting.
    """
    available = set(plugins.keys())
    for pid, meta in plugins.items():
        for dep in meta.dependencies:
            if not dep.optional and dep.plugin_id not in available:
                raise PluginDependencyError(f"Plugin {pid!r} requires missing dependency {dep.plugin_id!r}")
    graph = build_dependency_graph(plugins)
    return topological_sort(graph)
