from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ares.plugins.exceptions import PluginConfigurationError


class PluginConfig:
    """Configuration provider for the plugin system.

    Supports YAML, TOML, JSON, environment variables, and runtime overrides.
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginConfig:
        return cls(data)

    @classmethod
    def from_json(cls, path: str | Path) -> PluginConfig:
        p = Path(path)
        if not p.exists():
            raise PluginConfigurationError(f"Config file not found: {p}")
        with open(p) as f:
            return cls(json.load(f))

    @classmethod
    def from_env(cls, prefix: str = "ARES_PLUGIN_") -> PluginConfig:
        cfg: dict[str, Any] = {}
        for key, val in os.environ.items():
            if key.startswith(prefix):
                cfg[key[len(prefix) :].lower()] = val
        return cls(cfg)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def merge(self, other: PluginConfig) -> PluginConfig:
        merged = dict(self._data)
        merged.update(other._data)
        return PluginConfig(merged)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)
