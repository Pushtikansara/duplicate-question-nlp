"""Tests for DefaultConflictDetector."""

import pytest

from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.conflict_detector import (
    OPPOSITE_ACTION_PAIRS,
    DefaultConflictDetector,
)


@pytest.fixture
def detector():
    return DefaultConflictDetector()


class TestDefaultConflictDetector:
    def test_opposite_actions_detected(self, detector):
        rep_a = SemanticRepresentation(actions=["install"])
        rep_b = SemanticRepresentation(actions=["uninstall"])
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "opposite_actions" in types

    def test_opposite_actions_not_detected_for_same(self, detector):
        rep_a = SemanticRepresentation(actions=["install"])
        rep_b = SemanticRepresentation(actions=["install"])
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "opposite_actions" not in types

    def test_domain_mismatch(self, detector):
        rep_a = SemanticRepresentation(domain="technology")
        rep_b = SemanticRepresentation(domain="cooking")
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "domain_mismatch" in types

    def test_domain_match_no_conflict(self, detector):
        rep_a = SemanticRepresentation(domain="technology")
        rep_b = SemanticRepresentation(domain="technology")
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "domain_mismatch" not in types

    def test_low_confidence_detected(self, detector):
        rep_a = SemanticRepresentation(semantic_confidence=0.2)
        rep_b = SemanticRepresentation(semantic_confidence=0.9)
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "low_semantic_confidence" in types

    def test_contradictory_intent(self, detector):
        rep_a = SemanticRepresentation(intent_summary="install python")
        rep_b = SemanticRepresentation(intent_summary="uninstall python")
        conflicts = detector.detect(rep_a, rep_b)
        types = [c["conflict_type"] for c in conflicts]
        assert "contradictory_intent" in types

    def test_no_conflicts(self, detector):
        rep_a = SemanticRepresentation(
            actions=["install"],
            domain="technology",
            intent_summary="install python",
            semantic_confidence=0.9,
        )
        rep_b = SemanticRepresentation(
            actions=["install"],
            domain="technology",
            intent_summary="install python",
            semantic_confidence=0.9,
        )
        conflicts = detector.detect(rep_a, rep_b)
        assert len(conflicts) == 0

    def test_multiple_opposite_pairs(self, detector):
        rep_a = SemanticRepresentation(actions=["install", "create"])
        rep_b = SemanticRepresentation(actions=["uninstall", "delete"])
        conflicts = detector.detect(rep_a, rep_b)
        opposite_types = [c for c in conflicts if c["conflict_type"] == "opposite_actions"]
        assert len(opposite_types) >= 1

    def test_opposite_pairs_comprehensive(self):
        assert ("install", "uninstall") in OPPOSITE_ACTION_PAIRS
        assert ("create", "delete") in OPPOSITE_ACTION_PAIRS
        assert ("enable", "disable") in OPPOSITE_ACTION_PAIRS
        assert ("start", "stop") in OPPOSITE_ACTION_PAIRS
        assert ("upload", "download") in OPPOSITE_ACTION_PAIRS
        assert ("login", "logout") in OPPOSITE_ACTION_PAIRS
