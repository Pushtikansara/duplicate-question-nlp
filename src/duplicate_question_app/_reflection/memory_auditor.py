from __future__ import annotations

from typing import Any

from duplicate_question_app._reflection.interfaces import AuditorResult, MemoryAuditorABC


class MemoryAuditor(MemoryAuditorABC):
    def audit(self, memory_manager: Any, context: Any) -> AuditorResult:
        if memory_manager is None:
            return AuditorResult(
                module="memory",
                score=0.0,
                details={"available": False},
                warnings=["No memory manager available"],
                passed=False,
            )
        details: dict[str, Any] = {}
        warnings: list[str] = []
        score = 1.0

        try:
            stats = memory_manager.get_statistics()
            total = getattr(stats, "total_entries", 0)
            avg_quality = float(getattr(stats, "avg_quality", 0.0))
            avg_confidence = float(getattr(stats, "avg_confidence", 0.0))
            details["total_entries"] = total
            details["avg_quality"] = avg_quality
            details["avg_confidence"] = avg_confidence

            if total == 0:
                score -= 0.3
                warnings.append("Memory store is empty")
            if avg_quality < 0.3:
                score -= 0.2
                warnings.append(f"Low average memory quality: {avg_quality:.2f}")
            if avg_confidence < 0.3:
                score -= 0.15
                warnings.append(f"Low average memory confidence: {avg_confidence:.2f}")
        except Exception as e:
            score -= 0.5
            warnings.append(f"Could not access memory statistics: {e}")
            details["error"] = str(e)

        retrieved = getattr(context, "retrieved_memories", []) or []
        details["memories_retrieved"] = len(retrieved)
        if len(retrieved) == 0:
            score -= 0.1
            warnings.append("No memories retrieved for this prediction")

        score = max(0.0, min(1.0, score))
        return AuditorResult(
            module="memory",
            score=score,
            details=details,
            warnings=warnings,
            passed=score >= 0.5,
        )
