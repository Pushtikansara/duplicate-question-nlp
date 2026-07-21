from __future__ import annotations

import json
import tempfile
from pathlib import Path

from duplicate_question_app._routing.configuration import RoutingConfig, RoutingConfigLoader
from duplicate_question_app._routing.routing_strategy import RoutingStrategy


class TestRoutingConfig:
    def test_default_config_values(self):
        config = RoutingConfig()
        assert config.default_strategy == RoutingStrategy.BALANCED
        assert config.complexity_thresholds["medium_score"] == 0.4
        assert config.complexity_thresholds["complex_score"] == 0.7
        assert config.uncertainty_thresholds["escalation_confidence"] == 0.4
        assert config.uncertainty_thresholds["semantic_confidence"] == 0.5
        assert config.cost_limits["max_cost"] == 1.0
        assert config.latency_limits["max_latency_ms"] == 5000.0
        assert config.enable_cost_estimation is True
        assert config.enable_latency_estimation is True

    def test_custom_strategy(self):
        config = RoutingConfig(default_strategy=RoutingStrategy.FASTEST)
        assert config.default_strategy == RoutingStrategy.FASTEST

    def test_custom_thresholds(self):
        config = RoutingConfig(
            complexity_thresholds={"medium_score": 0.5, "complex_score": 0.8},
            uncertainty_thresholds={"escalation_confidence": 0.3, "semantic_confidence": 0.4},
        )
        assert config.complexity_thresholds["medium_score"] == 0.5
        assert config.uncertainty_thresholds["escalation_confidence"] == 0.3

    def test_disabled_estimations(self):
        config = RoutingConfig(enable_cost_estimation=False, enable_latency_estimation=False)
        assert config.enable_cost_estimation is False
        assert config.enable_latency_estimation is False

    def test_config_loader_from_dict_defaults(self):
        config = RoutingConfigLoader.from_dict({})
        assert config.default_strategy == RoutingStrategy.BALANCED
        assert config.enable_cost_estimation is True

    def test_config_loader_from_dict_custom(self):
        data = {
            "default_strategy": "fastest",
            "complexity_thresholds": {"medium_score": 0.3, "complex_score": 0.6},
            "enable_cost_estimation": False,
        }
        config = RoutingConfigLoader.from_dict(data)
        assert config.default_strategy == RoutingStrategy.FASTEST
        assert config.complexity_thresholds["medium_score"] == 0.3
        assert config.enable_cost_estimation is False

    def test_config_loader_from_dict_invalid_strategy(self):
        data = {"default_strategy": "invalid_strategy"}
        config = RoutingConfigLoader.from_dict(data)
        assert config.default_strategy == RoutingStrategy.BALANCED

    def test_config_loader_from_file(self):
        data = {
            "default_strategy": "highest_accuracy",
            "uncertainty_thresholds": {"escalation_confidence": 0.5, "semantic_confidence": 0.6},
            "enable_latency_estimation": False,
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            config = RoutingConfigLoader.from_file(f.name)
            assert config.default_strategy == RoutingStrategy.HIGHEST_ACCURACY
            assert config.uncertainty_thresholds["escalation_confidence"] == 0.5
            assert config.enable_latency_estimation is False
            Path(f.name).unlink()

    def test_config_loader_file_not_found(self):
        config = RoutingConfigLoader.from_file("/nonexistent/path/config.json")
        assert config.default_strategy == RoutingStrategy.BALANCED

    def test_config_loader_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            f.flush()
            config = RoutingConfigLoader.from_file(f.name)
            assert config.default_strategy == RoutingStrategy.BALANCED
            Path(f.name).unlink()
