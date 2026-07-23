from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from ares.memory.context import MemoryContext
from ares.memory.exceptions import MemorySessionError
from ares.memory.types import MemoryDomain, MemoryTier, MemoryValue

logger = logging.getLogger(__name__)


class MemorySession:
    def __init__(
        self,
        session_id: str = "",
        context: MemoryContext | None = None,
        ttl_seconds: float = 300.0,
    ) -> None:
        self._session_id = session_id or str(uuid.uuid4())
        self._context = context or MemoryContext()
        self._context.session_id = self._session_id
        self._started_at = time.time()
        self._ttl_seconds = ttl_seconds
        self._working_memory: dict[str, Any] = {}
        self._is_active = True

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def context(self) -> MemoryContext:
        return self._context

    @property
    def is_active(self) -> bool:
        if not self._is_active:
            return False
        elapsed = time.time() - self._started_at
        if elapsed > self._ttl_seconds:
            self._is_active = False
            return False
        return True

    @property
    def age_seconds(self) -> float:
        return time.time() - self._started_at

    def set_working(self, key: str, value: Any) -> None:
        self._working_memory[key] = value

    def get_working(self, key: str, default: Any = None) -> Any:
        return self._working_memory.get(key, default)

    def get_all_working(self) -> dict[str, Any]:
        return dict(self._working_memory)

    def clear_working(self) -> None:
        self._working_memory.clear()

    def to_memory_value(
        self,
        key: str,
        value: Any,
        tier: MemoryTier = MemoryTier.WORKING,
        domain: MemoryDomain = MemoryDomain.SEMANTIC,
    ) -> MemoryValue:
        return MemoryValue(
            key=key,
            value=value,
            tier=tier,
            domain=domain,
            agent_id=self._context.agent_id,
            session_id=self._session_id,
        )

    def close(self) -> None:
        self._is_active = False
        self._working_memory.clear()
        logger.debug("Session '%s' closed", self._session_id)

    def check_active(self) -> None:
        if not self.is_active:
            raise MemorySessionError(detail=f"Session '{self._session_id}' is expired or closed")
