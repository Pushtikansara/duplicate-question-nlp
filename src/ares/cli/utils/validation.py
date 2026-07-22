from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def validate_path(path: str | Path, must_exist: bool = True) -> Path:
    p = Path(path).resolve()
    if must_exist and not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    return p


def validate_file(path: str | Path) -> Path:
    p = validate_path(path)
    if not p.is_file():
        raise ValueError(f"Not a file: {p}")
    return p


def validate_directory(path: str | Path) -> Path:
    p = validate_path(path)
    if not p.is_dir():
        raise ValueError(f"Not a directory: {p}")
    return p


def validate_env_var(name: str) -> str | None:
    return os.environ.get(name)


def validate_positive_int(value: Any, name: str = "value") -> int:
    try:
        v = int(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{name} must be an integer, got {value!r}") from e
    if v <= 0:
        raise ValueError(f"{name} must be positive, got {v}")
    return v


def validate_float_range(value: Any, min_v: float = 0.0, max_v: float = 1.0, name: str = "value") -> float:
    try:
        v = float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{name} must be a float, got {value!r}") from e
    if v < min_v or v > max_v:
        raise ValueError(f"{name} must be between {min_v} and {max_v}, got {v}")
    return v


def validate_non_empty_string(value: Any, name: str = "value") -> str:
    s = str(value).strip()
    if not s:
        raise ValueError(f"{name} must not be empty")
    return s
