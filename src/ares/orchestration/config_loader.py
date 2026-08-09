from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ares.orchestration.strategy_registry import StrategyRegistry

_CONFIG_NAME = "orchestration"


def find_project_root() -> Path:
    """Locate the project root by walking up from this file.

    config_loader.py is at src/ares/orchestration/config_loader.py,
    so parents[3] reaches the project root.
    """
    return Path(__file__).resolve().parents[3]


def _find_config_dir(project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    return root / "configs"


def load_orchestration_yaml(
    config_dir: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Load ``configs/orchestration.yaml`` (returns ``{}`` when absent)."""
    directory = config_dir or _find_config_dir(project_root)
    filepath = directory / f"{_CONFIG_NAME}.yaml"
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        loaded = yaml.safe_load(f)
    return loaded if isinstance(loaded, dict) else {}


def build_strategy_registry(
    config_dir: Path | None = None,
    project_root: Path | None = None,
) -> StrategyRegistry:
    """Build the strategy registry from ``configs/orchestration.yaml``.

    Resolution order:

    1. If the file exists and declares non-empty ``strategy_defaults``,
       the registry is built from it.
    2. Otherwise the Phase 13 default strategy set is used
       (``StrategyRegistry.with_defaults()``).

    This keeps deployments without a config file working out of the box
    while making the mapping fully configuration-driven when the file is
    present.
    """
    config = load_orchestration_yaml(config_dir, project_root)
    defaults = config.get("strategy_defaults") or {}
    if defaults:
        return StrategyRegistry.from_config(config)
    return StrategyRegistry.with_defaults()
