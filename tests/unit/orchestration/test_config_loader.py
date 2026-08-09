from __future__ import annotations

from pathlib import Path

import pytest

from ares.orchestration.config_loader import build_strategy_registry, load_orchestration_yaml
from ares.orchestration.exceptions import InvalidStrategyConfigurationError

CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


class TestLoadOrchestrationYaml:
    def test_real_config_file_loaded(self):
        config = load_orchestration_yaml()
        assert isinstance(config, dict)
        assert "cache" in config
        assert "retry" in config
        assert "fallback" in config
        assert "strategy_defaults" in config

    def test_strategy_defaults_model_names(self):
        config = load_orchestration_yaml()
        defaults = config["strategy_defaults"]
        assert set(defaults) == {"fast_lexical", "baseline_classifier", "cross_encoder", "ensemble", "fallback"}
        assert defaults["fast_lexical"]["model"] == "TF-IDF + Logistic Regression (Week 2)"
        assert defaults["cross_encoder"]["model"] == "Cross-Encoder-Quora (Trained)"
        assert defaults["fallback"]["model"] == "Improved DistilBERT (Week 4)"

    def test_missing_directory_returns_empty(self, tmp_path: Path):
        assert load_orchestration_yaml(config_dir=tmp_path) == {}

    def test_missing_directory_builds_defaults(self, tmp_path: Path):
        registry = build_strategy_registry(config_dir=tmp_path)
        assert registry.list_strategies() == [
            "fast_lexical",
            "baseline_classifier",
            "cross_encoder",
            "ensemble",
            "fallback",
        ]
        assert registry.resolve("fallback").model_name == "Improved DistilBERT (Week 4)"

    def test_explicit_config_dir(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text("strategy_defaults:\n  custom:\n    model: Some Model\n")
        registry = build_strategy_registry(config_dir=tmp_path)
        assert registry.list_strategies() == ["custom"]
        assert registry.resolve("custom").model_name == "Some Model"

    def test_broken_config_raises(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text("strategy_defaults:\n  custom:\n    reflection: true\n")
        with pytest.raises(InvalidStrategyConfigurationError):
            build_strategy_registry(config_dir=tmp_path)


class TestConfigDrivenMappings:
    def test_registry_built_from_real_config(self):
        registry = build_strategy_registry()
        assert len(registry) == 5
        definitions = {d.name: d for d in registry.definitions()}
        assert definitions["fast_lexical"].use_reflection is False
        assert definitions["fast_lexical"].use_semantic_validation is False
        assert definitions["cross_encoder"].required_capabilities == frozenset({"cross_encoding"})
        assert definitions["fallback"].cache_enabled is True
