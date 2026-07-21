"""Plugin Loader — dynamically loads perception plugins.

Enables the engine to be extended with custom normalizers, tokenizers,
language detectors, and linguistic analyzers without modifying core code.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType
from typing import Any

from duplicate_question_app._config.logging_setup import get_logger
from duplicate_question_app._perception.config import PluginLoaderConfig
from duplicate_question_app._perception.exceptions import PluginLoadError

log = get_logger(__name__)


class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def initialize(self, config: dict[str, Any] | None = None) -> None: ...


class PluginLoader(ABC):
    @abstractmethod
    def load_plugin(self, module_name: str) -> list[Plugin]: ...

    @abstractmethod
    def discover_plugins(self, directory: str | Path) -> list[Plugin]: ...


class DefaultPluginLoader(PluginLoader):
    def __init__(self, config: PluginLoaderConfig | None = None):
        self._config = config or PluginLoaderConfig()
        self._logger = get_logger(f"{__name__}.DefaultPluginLoader")
        self._loaded: dict[str, Plugin] = {}

    def load_plugin(self, module_name: str) -> list[Plugin]:
        try:
            module = importlib.import_module(module_name)
            return self._extract_plugins(module)
        except ImportError as exc:
            raise PluginLoadError(
                f"Failed to load plugin module: {module_name}",
                context="plugin_loader",
                cause=str(exc),
                resolution=f"Ensure {module_name} is installed and importable",
            ) from exc

    def discover_plugins(self, directory: str | Path) -> list[Plugin]:
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise PluginLoadError(
                f"Plugin directory does not exist: {directory}",
                context="plugin_loader.discover",
                resolution=f"Ensure {directory} exists and is a directory",
            )
        plugins: list[Plugin] = []
        for _finder, name, _is_pkg in pkgutil.iter_modules([str(directory)]):
            try:
                module = importlib.import_module(name)
                found = self._extract_plugins(module)
                plugins.extend(found)
                self._logger.debug("Discovered plugin: %s (%d components)", name, len(found))
            except Exception as exc:
                self._logger.warning("Failed to load plugin %s: %s", name, exc)
        return plugins

    def _extract_plugins(self, module: ModuleType) -> list[Plugin]:
        plugins: list[Plugin] = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                try:
                    instance = obj()
                    instance.initialize()
                    plugins.append(instance)
                    self._loaded[instance.name] = instance
                except Exception as exc:
                    self._logger.warning("Failed to instantiate plugin %s: %s", name, exc)
        return plugins

    def get_loaded_plugins(self) -> dict[str, Plugin]:
        return dict(self._loaded)
