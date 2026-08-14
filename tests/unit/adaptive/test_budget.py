from __future__ import annotations

import pytest

from ares.adaptive.budget import BudgetPolicy
from ares.adaptive.models import ComputeBudget


def policy(cfg=None) -> BudgetPolicy:
    return BudgetPolicy(cfg)


class TestTierSelection:
    @pytest.mark.parametrize(
        ("difficulty", "risk", "expected"),
        [
            ("easy", "low", "low"),
            ("medium", "low", "medium"),
            ("easy", "medium", "medium"),
            ("hard", "low", "high"),
            ("critical", "low", "high"),
            ("easy", "high", "high"),
            ("easy", "critical", "high"),
        ],
    )
    def test_tier_for(self, difficulty, risk, expected):
        assert policy()._tier_for(difficulty, risk) == expected

    def test_allocate_returns_compute_budget(self):
        b = policy().allocate("medium", "medium")
        assert isinstance(b, ComputeBudget)
        assert b.name == "medium"

    def test_medium_tier_defaults(self):
        b = policy().allocate("medium", "low")
        assert b.max_model_calls >= 2
        assert b.max_escalation_level >= 1

    def test_low_tier_is_cheap(self):
        b = policy().allocate("easy", "low")
        assert b.max_model_calls == 1
        assert b.max_escalation_level == 0

    def test_high_tier_is_generous(self):
        b = policy().allocate("hard", "medium")
        assert b.max_model_calls >= 3
        assert b.max_escalation_level >= 2

    def test_tiers_configurable(self):
        cfg = {
            "budget": {
                "tiers": {
                    "low": {
                        "max_model_calls": 2,
                        "max_escalation_level": 0,
                        "max_latency_ms": 500,
                        "reflection_allowed": False,
                        "fusion_min_models": 0,
                    },
                    "medium": {
                        "max_model_calls": 3,
                        "max_escalation_level": 1,
                        "max_latency_ms": 1000,
                        "reflection_allowed": True,
                        "fusion_min_models": 0,
                    },
                    "high": {
                        "max_model_calls": 5,
                        "max_escalation_level": 4,
                        "max_latency_ms": 2000,
                        "reflection_allowed": True,
                        "fusion_min_models": 2,
                    },
                }
            }
        }
        b = policy(cfg).allocate("easy", "low")
        assert b.max_model_calls == 2

    def test_missing_tier_falls_back_to_defaults(self):
        cfg = {"budget": {"tiers": {"low": {}, "medium": {}, "high": {}}}}
        b = policy(cfg).allocate("easy", "low")
        assert b.max_model_calls == 1
        assert b.max_latency_ms == 1000
