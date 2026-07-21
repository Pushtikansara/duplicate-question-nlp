from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path

from ares.plugins.base import Plugin
from ares.plugins.exceptions import PluginLoadError


def discover_from_folder(folder: str | Path) -> list[type[Plugin]]:
    """Discover plugin classes by scanning a folder for importable modules.

    Each ``.py`` file in the folder is imported and inspected for
    ``Plugin`` subclasses.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        return []

    plugins: list[type[Plugin]] = []
    for item in folder_path.iterdir():
        if item.suffix != ".py" or item.name.startswith("_"):
            continue
        module_name = item.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, item)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Plugin) and obj is not Plugin:
                    plugins.append(obj)
        except Exception as exc:
            raise PluginLoadError(f"Failed to load plugin from {item}: {exc}") from exc

    return plugins


def discover_from_entrypoints(group: str = "ares.plugins") -> list[type[Plugin]]:
    """Discover plugins registered as Python entry points.

    Uses ``importlib.metadata.entry_points`` (Python 3.9+).
    """
    plugins: list[type[Plugin]] = []
    try:
        from importlib.metadata import entry_points

        eps = entry_points(group=group)
        for ep in eps:
            try:
                cls = ep.load()
                if inspect.isclass(cls) and issubclass(cls, Plugin) and cls is not Plugin:
                    plugins.append(cls)
            except Exception as exc:
                raise PluginLoadError(f"Failed to load entry point {ep.name}: {exc}") from exc
    except Exception:
        pass
    return plugins


def discover_from_namespace(package: str = "ares_plugins") -> list[type[Plugin]]:
    """Discover plugins installed as namespace packages.

    Scopes to packages whose name starts with ``package``.
    """
    plugins: list[type[Plugin]] = []
    try:
        pkg = importlib.import_module(package)
        pkg_path = getattr(pkg, "__path__", None)
        if pkg_path is None:
            return plugins
        for _importer, modname, _ispkg in pkgutil.iter_modules(pkg_path):
            try:
                mod = importlib.import_module(f"{package}.{modname}")
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin:
                        plugins.append(obj)
            except Exception:
                pass
    except ImportError:
        pass
    return plugins


def discover_all(
    folders: list[str | Path] | None = None,
    entrypoint_group: str = "ares.plugins",
    namespace_package: str = "ares_plugins",
) -> list[type[Plugin]]:
    """Aggregate discovery from all available sources."""
    found: list[type[Plugin]] = []
    if folders:
        for folder in folders:
            found.extend(discover_from_folder(folder))
    found.extend(discover_from_entrypoints(entrypoint_group))
    found.extend(discover_from_namespace(namespace_package))
    return found
