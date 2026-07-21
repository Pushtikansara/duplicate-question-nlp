"""ConflictDetector — detects conflicts between two SemanticRepresentations.

Detects:
  - Opposite actions (e.g., install vs uninstall)
  - Conflicting entities (same name, different type)
  - Domain mismatch
  - Contradictory intent
  - Low semantic confidence in either representation
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation

OPPOSITE_ACTION_PAIRS: list[tuple[str, str]] = [
    ("install", "uninstall"),
    ("install", "remove"),
    ("install", "delete"),
    ("setup", "teardown"),
    ("create", "delete"),
    ("create", "destroy"),
    ("add", "remove"),
    ("add", "delete"),
    ("enable", "disable"),
    ("start", "stop"),
    ("start", "halt"),
    ("begin", "end"),
    ("open", "close"),
    ("connect", "disconnect"),
    ("mount", "unmount"),
    ("attach", "detach"),
    ("load", "unload"),
    ("lock", "unlock"),
    ("hide", "show"),
    ("include", "exclude"),
    ("grant", "revoke"),
    ("allow", "deny"),
    ("increase", "decrease"),
    ("upgrade", "downgrade"),
    ("upload", "download"),
    ("import", "export"),
    ("push", "pull"),
    ("enter", "exit"),
    ("login", "logout"),
    ("compress", "decompress"),
    ("encrypt", "decrypt"),
    ("encode", "decode"),
    ("serialize", "deserialize"),
    ("merge", "split"),
    ("join", "leave"),
]


class DefaultConflictDetector:
    def __init__(self, opposite_pairs: list[tuple[str, str]] | None = None):
        self._opposite_pairs = opposite_pairs or OPPOSITE_ACTION_PAIRS

    def _is_opposite(self, action_a: str, action_b: str) -> bool:
        a = action_a.lower().strip()
        b = action_b.lower().strip()
        if a == b:
            return False
        return (a, b) in self._opposite_pairs or (b, a) in self._opposite_pairs

    def detect(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> list[dict]:
        conflicts = []

        actions_a = {a.lower().strip() for a in rep_a.actions}
        actions_b = {b.lower().strip() for b in rep_b.actions}

        for action_a in actions_a:
            for action_b in actions_b:
                if self._is_opposite(action_a, action_b):
                    conflicts.append(
                        {
                            "conflict_type": "opposite_actions",
                            "description": f"Action '{action_a}' in A is opposite to action '{action_b}' in B",
                            "severity": 0.9,
                            "source": "action_analysis",
                            "detail": {"action_a": action_a, "action_b": action_b},
                        }
                    )

        domain_a = rep_a.domain.lower().strip() if rep_a.domain else None
        domain_b = rep_b.domain.lower().strip() if rep_b.domain else None
        if domain_a and domain_b and domain_a != domain_b:
            conflicts.append(
                {
                    "conflict_type": "domain_mismatch",
                    "description": f"Domain mismatch: '{domain_a}' vs '{domain_b}'",
                    "severity": 0.7,
                    "source": "domain_analysis",
                    "detail": {"domain_a": rep_a.domain, "domain_b": rep_b.domain},
                }
            )

        summary_a = (rep_a.intent_summary or "").lower().strip()
        summary_b = (rep_b.intent_summary or "").lower().strip()
        if summary_a and summary_b and self._are_contradictory(summary_a, summary_b):
            conflicts.append(
                {
                    "conflict_type": "contradictory_intent",
                    "description": f"Contradictory intent: '{summary_a}' vs '{summary_b}'",
                    "severity": 0.85,
                    "source": "intent_analysis",
                    "detail": {"intent_a": summary_a, "intent_b": summary_b},
                }
            )

        if rep_a.semantic_confidence < 0.3:
            conflicts.append(
                {
                    "conflict_type": "low_semantic_confidence",
                    "description": f"Representation A has low semantic confidence: {rep_a.semantic_confidence:.2f}",
                    "severity": 0.5,
                    "source": "confidence_analysis",
                    "detail": {"confidence_a": rep_a.semantic_confidence},
                }
            )

        if rep_b.semantic_confidence < 0.3:
            conflicts.append(
                {
                    "conflict_type": "low_semantic_confidence",
                    "description": f"Representation B has low semantic confidence: {rep_b.semantic_confidence:.2f}",
                    "severity": 0.5,
                    "source": "confidence_analysis",
                    "detail": {"confidence_b": rep_b.semantic_confidence},
                }
            )

        return conflicts

    def _are_contradictory(self, summary_a: str, summary_b: str) -> bool:
        if summary_a == summary_b:
            return False
        words_a = set(summary_a.split())
        words_b = set(summary_b.split())
        for pair in self._opposite_pairs:
            if (pair[0] in words_a and pair[1] in words_b) or (pair[1] in words_a and pair[0] in words_b):
                return True
        negations = {"not", "never", "no", "without", "uninstall", "disable", "remove", "delete"}
        has_negation_a = bool(words_a & negations)
        has_negation_b = bool(words_b & negations)
        if has_negation_a != has_negation_b:
            common = words_a & words_b
            if len(common) >= 2:
                return True
        return False


ConflictDetector = DefaultConflictDetector
