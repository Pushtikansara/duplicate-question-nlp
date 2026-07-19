from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


ENV_PREFIX = "DQD_"

_config_cache: dict[str, dict[str, Any]] | None = None


def find_project_root() -> Path:
    """Find project root by walking up from this file.

    loader.py is at src/duplicate_question_app/_config/loader.py.
    parents[3] reaches the project root.
    """
    return Path(__file__).resolve().parents[3]


def _find_config_dir(project_root: Path | None = None) -> Path:
    """Locate the configs/ directory."""
    root = project_root or find_project_root()
    config_dir = root / "configs"
    if config_dir.exists():
        return config_dir

    env_override = os.environ.get(f"{ENV_PREFIX}CONFIG_DIR")
    if env_override:
        return Path(env_override)

    return config_dir


def _load_yaml(filepath: Path) -> dict[str, Any]:
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        return yaml.safe_load(f) or {}


def _merge_config(base: dict, override: dict) -> dict:
    """Deep merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict[str, Any], prefix: str = ENV_PREFIX) -> dict[str, Any]:
    """Walk config dict and override leaf values with env vars."""
    for key in list(config.keys()):
        env_key = f"{prefix}{key.upper()}"
        if env_key in os.environ:
            config[key] = _coerce(os.environ[env_key])
        if isinstance(config[key], dict):
            config[key] = _apply_env_overrides(config[key], prefix)
    return config


def _coerce(value: str) -> Any:
    """Coerce env var string to appropriate Python type."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    if value.lower() == "null" or value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_all_configs(
    config_dir: Path | None = None,
    project_root: Path | None = None,
    env: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Load all YAML config files, returning a dict keyed by config name.

    Supports:
    - Base YAML files from configs/
    - Environment variable overrides (DQD_*)
    - Optional env-specific YAML (configs/{env}.yaml)
    - Optional local override YAML (configs/local.yaml)
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if config_dir is None:
        config_dir = _find_config_dir(project_root)

    config_names = [
        "app", "paths", "models", "inference",
        "training", "evaluation", "dataset", "logging",
    ]

    merged: dict[str, dict[str, Any]] = {}
    for name in config_names:
        filepath = config_dir / f"{name}.yaml"
        cfg = _load_yaml(filepath)
        cfg = _apply_env_overrides(cfg)
        merged[name] = cfg

    # Apply env-specific override files
    env_name = env or os.environ.get(f"{ENV_PREFIX}ENV", "development")
    env_file = config_dir / f"{env_name}.yaml"
    if env_file.exists():
        env_cfg = _load_yaml(env_file)
        for name, cfg in env_cfg.items():
            if name in merged:
                merged[name] = _merge_config(merged[name], cfg)

    # Apply local override file (gitignored)
    local_file = config_dir / "local.yaml"
    if local_file.exists():
        local_cfg = _load_yaml(local_file)
        for name, cfg in local_cfg.items():
            if name in merged:
                merged[name] = _merge_config(merged[name], cfg)

    _config_cache = merged
    return merged


def get_config(
    section: str,
    config_dir: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Get a single config section (e.g. 'paths', 'models', 'inference')."""
    return load_all_configs(config_dir, project_root).get(section, {})


def get_env() -> str:
    return os.environ.get(f"{ENV_PREFIX}ENV", "development")


def clear_config_cache() -> None:
    global _config_cache
    _config_cache = None
