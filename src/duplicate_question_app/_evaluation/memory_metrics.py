from __future__ import annotations

from typing import Any


def compute_memory_metrics(memory_manager: Any) -> dict[str, Any]:
    if memory_manager is None:
        return {"available": False}
    try:
        stats = memory_manager.get_statistics()
    except Exception:
        return {"available": False, "error": "could not get statistics"}
    return {
        "available": True,
        "total_entries": getattr(stats, "total_entries", 0),
        "total_by_type": getattr(stats, "total_by_type", {}),
        "avg_quality": float(getattr(stats, "avg_quality", 0.0)),
        "avg_confidence": float(getattr(stats, "avg_confidence", 0.0)),
        "deleted_count": getattr(stats, "deleted_count", 0),
    }
