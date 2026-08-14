from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

_CONFIG_NAME = "adaptive_routing"


def find_project_root() -> Path:
    """Adaptive package lives at src/ares/adaptive/, parents[3] is repo root."""
    return Path(__file__).resolve().parents[3]


def load_adaptive_config(config_dir: Path | None = None, project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or find_project_root()
    directory = config_dir or root / "configs"
    filepath = directory / f"{_CONFIG_NAME}.yaml"
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        loaded = yaml.safe_load(f)
    return loaded if isinstance(loaded, dict) else {}


def _deep_get(mapping: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


class AdaptiveRoutingConfig:
    """Typed accessor over the ``configs/adaptive_routing.yaml`` payload.

    Every routing threshold is read from here: no magic numbers live in the
    router.  Missing keys fall back to the documented defaults.
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {}

    @property
    def enabled(self) -> bool:
        return bool(self._data.get("enabled", False))

    @property
    def difficulty_thresholds(self) -> dict[str, Any]:
        return _deep_get(self._data, "difficulty", "thresholds", default={}) or {}

    @property
    def difficulty_weights(self) -> dict[str, Any]:
        default = {
            "lexical": 0.25,
            "negation": 0.15,
            "contradiction": 0.20,
            "ambiguity": 0.15,
            "abbreviation": 0.05,
            "numeric_conflict": 0.05,
            "length": 0.05,
            "cheap_confidence": 0.10,
        }
        return _deep_get(self._data, "difficulty", "weights", default=default) or default

    @property
    def difficulty_boosts(self) -> dict[str, Any]:
        default = {
            "contradiction": {"signal_min": 0.5, "min_score": 0.55},
            "negation_overlap": {"signal_min": 0.5, "min_score": 0.45},
            "ambiguity": {"signal_min": 0.9, "min_score": 0.40},
            "numeric_conflict": {"signal_min": 0.9, "min_score": 0.40},
            "abbreviation": {"signal_min": 0.5, "min_score": 0.45},
            "content_gap": {"overlap_min": 0.45, "content_max": 0.35, "gap_min": 0.15, "min_score": 0.45},
        }
        return _deep_get(self._data, "difficulty", "boosts", default=default) or default

    @property
    def difficulty_acronyms(self) -> dict[str, Any]:
        return _deep_get(self._data, "difficulty", "acronyms", default={}) or {}

    @property
    def confidence_high(self) -> float:
        return float(_deep_get(self._data, "confidence", "high", default=0.85))

    @property
    def confidence_medium(self) -> float:
        return float(_deep_get(self._data, "confidence", "medium", default=0.60))

    @property
    def confidence_min_evident(self) -> float:
        return float(_deep_get(self._data, "confidence", "min_evident", default=0.45))

    @property
    def escalation_enabled(self) -> bool:
        return bool(_deep_get(self._data, "escalation", "enabled", default=True))

    @property
    def escalation_max_levels(self) -> int:
        return int(_deep_get(self._data, "escalation", "max_levels", default=3))

    @property
    def trust_escalation_enabled(self) -> bool:
        return bool(_deep_get(self._data, "trust", "escalation_enabled", default=True))

    @property
    def trust_max_extra_models(self) -> int:
        return int(_deep_get(self._data, "trust", "max_extra_models", default=1))

    @property
    def trust_high_threshold(self) -> float:
        return float(_deep_get(self._data, "trust", "high_threshold", default=0.70))

    @property
    def trust_low_threshold(self) -> float:
        return float(_deep_get(self._data, "trust", "low_threshold", default=0.40))

    @property
    def trust_reliability_min(self) -> float:
        return float(_deep_get(self._data, "trust", "reliability_min", default=0.70))

    @property
    def trust_abbreviation_relation_min(self) -> float:
        return float(_deep_get(self._data, "trust", "abbreviation_relation_min", default=0.50))

    @property
    def trust_content_mismatch_max(self) -> float:
        return float(_deep_get(self._data, "trust", "content_mismatch_max", default=0.15))

    @property
    def trust_escalation_reasons(self) -> list[str]:
        return list(_deep_get(self._data, "trust", "escalation_reasons", default=[]) or [])

    @property
    def early_exit_enabled(self) -> bool:
        return bool(_deep_get(self._data, "early_exit", "enabled", default=True))

    @property
    def early_exit_high_confidence_threshold(self) -> float:
        return float(_deep_get(self._data, "early_exit", "high_confidence_threshold", default=0.90))

    @property
    def early_exit_only_low_risk(self) -> bool:
        return bool(_deep_get(self._data, "early_exit", "only_low_risk", default=True))

    @property
    def reflection_mode(self) -> str:
        return str(_deep_get(self._data, "reflection", "mode", default="conditional"))

    @property
    def reflection_hard_difficulty_only(self) -> bool:
        return bool(_deep_get(self._data, "reflection", "hard_difficulty_only", default=True))

    @property
    def fusion_enabled(self) -> bool:
        return bool(_deep_get(self._data, "fusion", "enabled", default=True))

    @property
    def fusion_min_models(self) -> int:
        return int(_deep_get(self._data, "fusion", "min_models", default=2))

    @property
    def fusion_method(self) -> str:
        return str(_deep_get(self._data, "fusion", "method", default="confidence_weighted"))

    @property
    def fusion_model_names(self) -> list[str]:
        return list(_deep_get(self._data, "fusion", "model_names", default=[]) or [])

    @property
    def budget_tiers(self) -> dict[str, Any]:
        default = {
            "low": {
                "max_model_calls": 1,
                "max_escalation_level": 0,
                "max_latency_ms": 1000,
                "reflection_allowed": False,
                "fusion_min_models": 0,
            },
            "medium": {
                "max_model_calls": 2,
                "max_escalation_level": 1,
                "max_latency_ms": 3000,
                "reflection_allowed": True,
                "fusion_min_models": 0,
            },
            "high": {
                "max_model_calls": 4,
                "max_escalation_level": 3,
                "max_latency_ms": 15000,
                "reflection_allowed": True,
                "fusion_min_models": 2,
            },
        }
        return _deep_get(self._data, "budget", "tiers", default=default) or default

    @property
    def model_profiles(self) -> dict[str, Any]:
        return _deep_get(self._data, "model_profiles", default={}) or {}


def make_config_path(config_dir: Path | None = None, project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    directory = config_dir or root / "configs"
    return directory / f"{_CONFIG_NAME}.yaml"


def ensure_config_file(config_dir: Path | None = None, project_root: Path | None = None) -> Path:
    """Create ``configs/adaptive_routing.yaml`` from the built-in defaults when
    the file is absent, so deployments always see the full parameter surface."""
    path = make_config_path(config_dir, project_root)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    # Import lazily to avoid a circular import at module load time.
    from ares.adaptive.defaults import DEFAULT_ADAPTIVE_CONFIG

    path.write_text(yaml.safe_dump(DEFAULT_ADAPTIVE_CONFIG, sort_keys=False, indent=2))
    return path


if __name__ == "__main__":
    sys.stdout.write(ensure_config_file().__str__() + "\n")
