from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from duplicate_question_app._memory.interfaces import MemoryAudit

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    timestamp: datetime
    memory_id: str
    action: str
    module: str
    details: str = ""


class DefaultMemoryAudit(MemoryAudit):
    def __init__(self) -> None:
        self._log: list[AuditEntry] = []
        self._lock = threading.Lock()

    def log_access(self, memory_id: str, action: str, module: str, details: str = "") -> None:
        entry = AuditEntry(
            timestamp=datetime.now(),
            memory_id=memory_id,
            action=action,
            module=module,
            details=details,
        )
        with self._lock:
            self._log.append(entry)
            logger.debug("Audit: %s %s on %s from %s", action, memory_id, module, details)

    def get_history(self, memory_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                }
                for e in self._log
                if e.memory_id == memory_id
            ]

    def get_recent_actions(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            recent = self._log[-limit:]
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "memory_id": e.memory_id,
                    "action": e.action,
                    "module": e.module,
                    "details": e.details,
                }
                for e in recent
            ]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total = len(self._log)
            action_counts: dict[str, int] = {}
            module_counts: dict[str, int] = {}
            for e in self._log:
                action_counts[e.action] = action_counts.get(e.action, 0) + 1
                module_counts[e.module] = module_counts.get(e.module, 0) + 1
            return {
                "total_actions": total,
                "action_counts": action_counts,
                "module_counts": module_counts,
            }

    def clear(self) -> None:
        with self._lock:
            self._log.clear()
            logger.debug("Audit log cleared")
