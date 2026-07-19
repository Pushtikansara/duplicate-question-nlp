"""Device resolution — single source of truth for CPU/CUDA selection.

Two different ``_resolve_device`` helpers existed in the original codebase
with different default behaviour (auto-detect vs always-force-CPU).
This module provides both variants explicitly named so callers can
choose the appropriate policy.
"""

from __future__ import annotations

import torch


def resolve_device(force_cpu: bool = False) -> str:
    """Resolve the compute device.

    Args:
        force_cpu: If True, always return ``"cpu"`` (avoids CUDA OOM).
                   If False, auto-detect CUDA availability.

    Returns:
        ``"cuda"`` or ``"cpu"``.
    """
    if force_cpu:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def resolve_device_safe() -> str:
    """Resolve device, forcing CPU to avoid OOM on shared infra.

    Equivalent to ``resolve_device(force_cpu=True)``.
    """
    return "cpu"
