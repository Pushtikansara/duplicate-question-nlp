from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Phase 14 default adaptive-routing configuration.
#
# Every threshold is configurable and shipped in configs/adaptive_routing.yaml
# (this dict is written out by config_loader.ensure_config_file when the file
# is missing).  Defaults were chosen to be conservative and deterministic;
# production tuning should happen through the YAML file, never source code.
# ---------------------------------------------------------------------------


DEFAULT_ADAPTIVE_CONFIG: dict[str, Any] = {
    "enabled": False,
    "difficulty": {
        "thresholds": {"easy_max": 0.33, "medium_max": 0.60, "hard_max": 0.80},
        "weights": {
            "lexical": 0.25,
            "negation": 0.15,
            "contradiction": 0.20,
            "ambiguity": 0.15,
            "abbreviation": 0.05,
            "numeric_conflict": 0.05,
            "length": 0.05,
            "cheap_confidence": 0.10,
        },
        "boosts": {
            "contradiction": {"signal_min": 0.5, "min_score": 0.55},
            "negation_overlap": {"signal_min": 0.5, "min_score": 0.45},
            "ambiguity": {"signal_min": 0.9, "min_score": 0.40},
            "numeric_conflict": {"signal_min": 0.9, "min_score": 0.40},
            "abbreviation": {"signal_min": 0.5, "min_score": 0.45},
            "abbreviation_relation": {"signal_min": 0.5, "min_score": 0.45},
            "content_gap": {"overlap_min": 0.45, "content_max": 0.35, "gap_min": 0.15, "min_score": 0.45},
        },
        "acronyms": {
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "nlp": "natural language processing",
            "nl": "natural language",
            "dl": "deep learning",
            "cv": "computer vision",
            "api": "application programming interface",
            "ui": "user interface",
            "ux": "user experience",
            "os": "operating system",
            "gpu": "graphics processing unit",
            "cpu": "central processing unit",
            "ram": "random access memory",
            "db": "database",
            "cnn": "convolutional neural network",
            "svm": "support vector machine",
            "html": "hyper text markup language",
        },
    },
    "confidence": {"high": 0.85, "medium": 0.60, "min_evident": 0.45},
    "escalation": {"enabled": True, "max_levels": 3},
    "trust": {
        "escalation_enabled": True,
        "max_extra_models": 1,
        "high_threshold": 0.70,
        "low_threshold": 0.40,
        "reliability_min": 0.70,
        "abbreviation_relation_min": 0.50,
        "content_mismatch_max": 0.15,
    },
    "early_exit": {"enabled": True, "high_confidence_threshold": 0.90, "only_low_risk": True},
    "reflection": {"mode": "conditional", "hard_difficulty_only": True},
    "fusion": {"enabled": True, "min_models": 2, "method": "confidence_weighted", "model_names": []},
    "budget": {
        "tiers": {
            "low": {
                "max_model_calls": 1,
                "max_escalation_level": 0,
                "max_latency_ms": 1000,
                "reflection_allowed": False,
                "fusion_min_models": 0,
            },
            "medium": {
                "max_model_calls": 2,
                "max_escalation_level": 1,
                "max_latency_ms": 3000,
                "reflection_allowed": True,
                "fusion_min_models": 0,
            },
            "high": {
                "max_model_calls": 4,
                "max_escalation_level": 3,
                "max_latency_ms": 15000,
                "reflection_allowed": True,
                "fusion_min_models": 2,
            },
        }
    },
    "model_profiles": {
        "week2_lr": {
            "expected_accuracy": 0.72,
            "expected_latency_ms": 1.0,
            "computational_cost": 1.0,
            "confidence_quality": 0.5,
        },
        "week2_svm": {
            "expected_accuracy": 0.70,
            "expected_latency_ms": 1.1,
            "computational_cost": 1.0,
            "confidence_quality": 0.5,
        },
        "week3": {
            "expected_accuracy": 0.81,
            "expected_latency_ms": 3.5,
            "computational_cost": 5.0,
            "confidence_quality": 0.65,
        },
        "week4": {
            "expected_accuracy": 0.82,
            "expected_latency_ms": 3.3,
            "computational_cost": 5.0,
            "confidence_quality": 0.65,
        },
        "bge": {
            "expected_accuracy": 0.80,
            "expected_latency_ms": 5.0,
            "computational_cost": 4.0,
            "confidence_quality": 0.6,
        },
        "e5": {
            "expected_accuracy": 0.79,
            "expected_latency_ms": 5.0,
            "computational_cost": 4.0,
            "confidence_quality": 0.6,
        },
        "e5_ft": {
            "expected_accuracy": 0.83,
            "expected_latency_ms": 6.0,
            "computational_cost": 5.0,
            "confidence_quality": 0.65,
        },
        "mpnet": {
            "expected_accuracy": 0.83,
            "expected_latency_ms": 5.0,
            "computational_cost": 4.0,
            "confidence_quality": 0.65,
        },
        "deberta": {
            "expected_accuracy": 0.84,
            "expected_latency_ms": 25.0,
            "computational_cost": 10.0,
            "confidence_quality": 0.75,
        },
        "ce_quora": {
            "expected_accuracy": 0.87,
            "expected_latency_ms": 21.0,
            "computational_cost": 10.0,
            "confidence_quality": 0.8,
        },
        "ensemble": {
            "expected_accuracy": 0.88,
            "expected_latency_ms": 30.0,
            "computational_cost": 25.0,
            "confidence_quality": 0.8,
        },
    },
}
