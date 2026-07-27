from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ENV_PREFIX = "DQD_"

_config_cache: dict[str, dict[str, Any]] | None = None


def find_project_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    env_override = os.environ.get(f"{ENV_PREFIX}PROJECT_ROOT")
    if env_override:
        root = Path(env_override)
    return root


def _find_config_dir(project_root: Path | None = None) -> Path:
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
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict[str, Any], prefix: str = ENV_PREFIX) -> dict[str, Any]:
    for key in list(config.keys()):
        env_key = f"{prefix}{key.upper()}"
        if env_key in os.environ:
            config[key] = _coerce(os.environ[env_key])
        if isinstance(config[key], dict):
            config[key] = _apply_env_overrides(config[key], prefix)
    return config


def _coerce(value: str) -> Any:
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    if value.lower() in ("null", "none"):
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
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if config_dir is None:
        config_dir = _find_config_dir(project_root)

    config_names = [
        "app",
        "paths",
        "models",
        "inference",
        "training",
        "evaluation",
        "dataset",
        "logging",
    ]

    merged: dict[str, dict[str, Any]] = {}
    for name in config_names:
        filepath = config_dir / f"{name}.yaml"
        cfg = _load_yaml(filepath)
        cfg = _apply_env_overrides(cfg)
        merged[name] = cfg

    env_name = env or os.environ.get(f"{ENV_PREFIX}ENV", "development")
    env_file = config_dir / f"{env_name}.yaml"
    if env_file.exists():
        env_cfg = _load_yaml(env_file)
        for name, cfg in env_cfg.items():
            if name in merged:
                merged[name] = _merge_config(merged[name], cfg)

    local_file = config_dir / "local.yaml"
    if local_file.exists():
        local_cfg = _load_yaml(local_file)
        for name, cfg in local_cfg.items():
            if name in merged:
                merged[name] = _merge_config(merged[name], cfg)

    _config_cache = merged
    return merged


def get_config(section: str) -> dict[str, Any]:
    return load_all_configs().get(section, {})


def clear_config_cache() -> None:
    global _config_cache
    _config_cache = None


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    data_dir: Path
    models_dir: Path
    results_dir: Path
    notebooks_dir: Path
    cache_dir: Path
    logs_dir: Path
    output_dir: Path
    exports_dir: Path
    week3_model_dir: Path
    week4_model_dir: Path
    transformer_results_dir: Path
    week4_results_dir: Path
    baseline_results_dir: Path
    bge_model_dir: Path
    e5_model_dir: Path
    mpnet_model_dir: Path
    deberta_model_dir: Path
    finetuned_e5_dir: Path
    finetuned_bge_dir: Path
    finetuned_cross_encoder_dir: Path


def get_app_paths(project_root: Path | None = None) -> AppPaths:
    root = project_root or find_project_root()
    env_root = os.environ.get(f"{ENV_PREFIX}PROJECT_ROOT")
    if env_root:
        root = Path(env_root)
    paths_cfg = get_config("paths")
    if not paths_cfg:
        return _legacy_get_app_paths(root)

    def _resolve_path(key: str, default: str | None = None) -> Path:
        override = os.environ.get(f"{ENV_PREFIX}{key.upper()}")
        if override:
            p = Path(override)
            return p if p.is_absolute() else root / p
        val = paths_cfg.get(key)
        if val is None:
            if default:
                return root / default
            return root
        p = Path(str(val))
        return p if p.is_absolute() else root / p

    return AppPaths(
        project_root=root,
        data_dir=_resolve_path("data_dir", "data"),
        models_dir=_resolve_path("models_dir", "models"),
        results_dir=_resolve_path("results_dir", "outputs"),
        notebooks_dir=_resolve_path("notebooks_dir", "notebooks"),
        cache_dir=_resolve_path("cache_dir", "cache"),
        logs_dir=_resolve_path("logs_dir", "logs"),
        output_dir=_resolve_path("output_dir", "outputs"),
        exports_dir=_resolve_path("exports_dir", "exports"),
        week3_model_dir=_resolve_path("week3_model_dir", "models/saved_transformer_model"),
        week4_model_dir=_resolve_path("week4_model_dir", "models/week4_improved_model"),
        transformer_results_dir=_resolve_path("transformer_results_dir", "outputs/transformer_model"),
        week4_results_dir=_resolve_path("week4_results_dir", "outputs/week4_improvement"),
        baseline_results_dir=_resolve_path("baseline_results_dir", "outputs/baseline_model"),
        bge_model_dir=_resolve_path("bge_model_dir", "models/bge_base_en_v1_5"),
        e5_model_dir=_resolve_path("e5_model_dir", "models/e5_base_v2"),
        mpnet_model_dir=_resolve_path("mpnet_model_dir", "models/mpnet_base_v2"),
        deberta_model_dir=_resolve_path("deberta_model_dir", "models/deberta_v3_cross_encoder"),
        finetuned_e5_dir=_resolve_path("finetuned_e5_dir", "models/e5-quora-finetuned"),
        finetuned_bge_dir=_resolve_path("finetuned_bge_dir", "models/bge-quora-finetuned"),
        finetuned_cross_encoder_dir=_resolve_path("finetuned_cross_encoder_dir", "models/cross-encoder-quora"),
    )


def _legacy_get_app_paths(root: Path | None = None) -> AppPaths:
    if root is None:
        root = find_project_root()
    data_override = os.environ.get(f"{ENV_PREFIX}DATA_DIR")
    data_dir = Path(data_override) if data_override else root / "data"
    return AppPaths(
        project_root=root,
        data_dir=data_dir,
        models_dir=root / "models",
        results_dir=root / "outputs",
        notebooks_dir=root / "notebooks",
        cache_dir=root / "cache",
        logs_dir=root / "logs",
        output_dir=root / "outputs",
        exports_dir=root / "exports",
        week3_model_dir=root / "models" / "saved_transformer_model",
        week4_model_dir=root / "models" / "week4_improved_model",
        transformer_results_dir=root / "outputs" / "transformer_model",
        week4_results_dir=root / "outputs" / "week4_improvement",
        baseline_results_dir=root / "outputs" / "baseline_model",
        bge_model_dir=root / "models" / "bge_base_en_v1_5",
        e5_model_dir=root / "models" / "e5_base_v2",
        mpnet_model_dir=root / "models" / "mpnet_base_v2",
        deberta_model_dir=root / "models" / "deberta_v3_cross_encoder",
        finetuned_e5_dir=root / "models" / "e5-quora-finetuned",
        finetuned_bge_dir=root / "models" / "bge-quora-finetuned",
        finetuned_cross_encoder_dir=root / "models" / "cross-encoder-quora",
    )


def ensure_directories(paths: AppPaths) -> list[str]:
    warnings: list[str] = []
    dirs = [
        paths.models_dir,
        paths.data_dir,
        paths.results_dir,
        paths.notebooks_dir,
        paths.cache_dir,
        paths.logs_dir,
        paths.output_dir,
        paths.exports_dir,
    ]
    for d in dirs:
        if not d.exists():
            try:
                d.mkdir(parents=True, exist_ok=True)
            except OSError:
                warnings.append(f"Could not create directory: {d}")
    return warnings


def resolve_device() -> str:
    cfg = get_config("inference") or {}
    if not cfg.get("auto_device", True):
        return str(cfg.get("default_device", "cpu"))
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"
