from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ares.api.dependencies import get_request_id, require_user
from ares.api.models import MemoryEntry, MemoryQuery

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/memory", response_model=list[MemoryEntry], dependencies=[Depends(require_user)])
async def list_memory(
    memory_type: str | None = Query(None),
    limit: int = Query(default=10, ge=1, le=100),
    request_id: str = Depends(get_request_id),
) -> list[MemoryEntry]:
    entries: list[MemoryEntry] = []
    try:
        from duplicate_question_app._memory.memory_manager import MemoryManager

        mm = MemoryManager()
        all_entries = mm.list(memory_type=memory_type) if hasattr(mm, "list") else []
        for e in all_entries[:limit]:
            entries.append(
                MemoryEntry(
                    id=str(getattr(e, "id", "")),
                    type=str(getattr(e, "type", "unknown")),
                    content=getattr(e, "content", {}) if hasattr(e, "content") else {},
                    confidence=getattr(e, "confidence", 0.0),
                    created_at=getattr(e, "created_at", __import__("datetime").datetime.now()),
                    last_accessed=getattr(e, "last_accessed", __import__("datetime").datetime.now()),
                    access_count=getattr(e, "access_count", 0),
                    tags=list(getattr(e, "tags", [])),
                )
            )
    except Exception as e:
        logger.warning("Memory list failed: %s", e)
    return entries


@router.post("/memory/search", response_model=list[MemoryEntry], dependencies=[Depends(require_user)])
async def search_memory(
    query: MemoryQuery,
    request_id: str = Depends(get_request_id),
) -> list[MemoryEntry]:
    entries: list[MemoryEntry] = []
    try:
        from duplicate_question_app._memory.memory_manager import MemoryManager

        mm = MemoryManager()
        results: Any = mm.search(query) if hasattr(mm, "search") else []
        for e in results:
            entries.append(
                MemoryEntry(
                    id=str(getattr(e, "id", "")),
                    type=str(getattr(e, "type", "unknown")),
                    content=getattr(e, "content", {}),
                    confidence=getattr(e, "confidence", 0.0),
                    created_at=getattr(e, "created_at", __import__("datetime").datetime.now()),
                    last_accessed=getattr(e, "last_accessed", __import__("datetime").datetime.now()),
                    access_count=getattr(e, "access_count", 0),
                    tags=list(getattr(e, "tags", [])),
                )
            )
    except Exception as e:
        logger.warning("Memory search failed: %s", e)
    return entries


@router.get("/memory/stats", dependencies=[Depends(require_user)])
async def memory_stats(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    try:
        from duplicate_question_app._memory.memory_statistics import MemoryStatistics

        ms = MemoryStatistics()  # type: ignore[call-arg]
        return ms.get_stats() if hasattr(ms, "get_stats") else {"status": "unavailable"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.post("/memory/clean", dependencies=[Depends(require_user)])
async def clean_memory(
    force: bool = False,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    try:
        from duplicate_question_app._memory.memory_consolidator import MemoryConsolidator

        mc: Any = MemoryConsolidator()  # type: ignore[abstract]
        result = mc.consolidate()
        return {"status": "ok", "result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
