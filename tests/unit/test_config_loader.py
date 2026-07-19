from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from duplicate_question_app._config.loader import (
    _apply_env_overrides,
    _coerce,
    _merge_config,
    clear_config_cache,
    get_config,
    get_env,
    load_all_configs,
)
from duplicate_question_app._config.settings import get_app_paths

SAMPLE_APP_YAML = {
    "default_model": "E5-base-v2",
    "default_threshold": 0.5,
    "default_device": "cpu",
}


class TestConfigLoader:
    def test_coerce_bool_true(self):
        assert _coerce("true") is True
        assert _coerce("True") is True
        assert _coerce("1") is True
        assert _coerce("yes") is True

    def test_coerce_bool_false(self):
        assert _coerce("false") is False
        assert _coerce("False") is False
        assert _coerce("0") is False
        assert _coerce("no") is False

    def test_coerce_null(self):
        assert _coerce("null") is None
        assert _coerce("none") is None
        assert _coerce("None") is None

    def test_coerce_int(self):
        assert _coerce("42") == 42
        assert _coerce("-5") == -5

    def test_coerce_float(self):
        assert _coerce("3.14") == 3.14
        assert _coerce("0.5") == 0.5

    def test_coerce_string(self):
        assert _coerce("hello") == "hello"
        assert _coerce("") == ""

    def test_merge_config_simple(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _merge_config(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_config_nested(self):
        base = {"outer": {"inner1": 1, "inner2": 2}}
        override = {"outer": {"inner1": 99}}
        result = _merge_config(base, override)
        assert result["outer"]["inner1"] == 99
        assert result["outer"]["inner2"] == 2

    def test_apply_env_overrides_top_level(self):
        os.environ["DQD_MODEL_NAME"] = "test-model"
        config = {"model_name": "default", "threshold": 0.5}
        result = _apply_env_overrides(config)
        assert result["model_name"] == "test-model"
        assert result["threshold"] == 0.5
        os.environ.pop("DQD_MODEL_NAME")

    def test_apply_env_overrides_nested(self):
        os.environ["DQD_DEFAULT_THRESHOLD"] = "0.75"
        config = {"default_threshold": 0.5, "inner": {"flag": True}}
        result = _apply_env_overrides(config)
        assert result["default_threshold"] == 0.75
        os.environ.pop("DQD_DEFAULT_THRESHOLD")

    def test_apply_env_overrides_nested_dict(self):
        os.environ["DQD_BATCH_SIZE"] = "64"
        config = {"batch_size": 32, "nested": {"batch_size": 16}}
        result = _apply_env_overrides(config)
        assert result["batch_size"] == 64
        os.environ.pop("DQD_BATCH_SIZE")

    def test_load_all_configs_loads_all_sections(self):
        cfg = load_all_configs()
        assert "app" in cfg
        assert "paths" in cfg
        assert "models" in cfg
        assert "inference" in cfg
        assert "training" in cfg
        assert "evaluation" in cfg
        assert "dataset" in cfg
        assert "logging" in cfg

    def test_load_all_configs_caching(self):
        clear_config_cache()
        cfg1 = load_all_configs()
        cfg2 = load_all_configs()
        assert cfg1 is cfg2
        clear_config_cache()

    def test_load_all_configs_returns_copy(self):
        clear_config_cache()
        cfg = load_all_configs()
        assert isinstance(cfg, dict)

    def test_get_config_returns_section(self):
        app_cfg = get_config("app")
        assert "default_model" in app_cfg

    def test_get_config_missing_section(self):
        result = get_config("nonexistent")
        assert result == {}

    def test_get_env_default(self):
        env = get_env()
        assert env == "development"

    def test_get_env_override(self):
        os.environ["DQD_ENV"] = "production"
        assert get_env() == "production"
        os.environ.pop("DQD_ENV")

    def test_clear_config_cache(self):
        clear_config_cache()
        assert load_all_configs() is not None

    def test_with_temp_config_dir(self):
        clear_config_cache()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            test_cfg = {"my_key": "my_value"}
            with open(config_dir / "app.yaml", "w") as f:
                yaml.dump(test_cfg, f)
            for name in ["paths", "models", "inference", "training", "evaluation", "dataset", "logging"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            cfg = load_all_configs(config_dir=config_dir)
            assert cfg["app"]["my_key"] == "my_value"


class TestConfigSettings:
    def test_get_app_paths_returns_app_paths(self):
        paths = get_app_paths()
        assert paths.project_root.exists()
        assert hasattr(paths, "data_dir")
        assert hasattr(paths, "models_dir")
        assert hasattr(paths, "results_dir")
        assert hasattr(paths, "week3_model_dir")
        assert hasattr(paths, "week4_model_dir")

    def test_get_app_paths_overrides(self):
        os.environ["DQD_DATA_DIR"] = "/tmp/test_data_dir"
        paths = get_app_paths()
        assert str(paths.data_dir) == "/tmp/test_data_dir"
        os.environ.pop("DQD_DATA_DIR")

    def test_get_app_paths_absolute_override(self):
        os.environ["DQD_PROJECT_ROOT"] = "/tmp"
        paths = get_app_paths()
        assert str(paths.project_root) == "/tmp"
        os.environ.pop("DQD_PROJECT_ROOT")

    def test_model_choices_loaded(self):
        from duplicate_question_app._config.settings import MODEL_CHOICES

        assert "E5-base-v2" in MODEL_CHOICES
        assert "Semantic Ensemble" in MODEL_CHOICES

    def test_is_transformer_model(self):
        from duplicate_question_app._config.settings import is_transformer_model

        assert is_transformer_model("DistilBERT (Week 3)") is True
        assert is_transformer_model("E5-base-v2") is False

    def test_is_sentence_transformer_model(self):
        from duplicate_question_app._config.settings import is_sentence_transformer_model

        assert is_sentence_transformer_model("E5-base-v2") is True
        assert is_sentence_transformer_model("DistilBERT (Week 3)") is False

    def test_is_cross_encoder_model(self):
        from duplicate_question_app._config.settings import is_cross_encoder_model

        assert is_cross_encoder_model("DeBERTa-v3 Cross-Encoder") is True
        assert is_cross_encoder_model("E5-base-v2") is False

    def test_is_ensemble_model(self):
        from duplicate_question_app._config.settings import is_ensemble_model

        assert is_ensemble_model("Semantic Ensemble") is True
        assert is_ensemble_model("E5-base-v2") is False

    def test_is_new_embedding_model(self):
        from duplicate_question_app._config.settings import is_new_embedding_model

        assert is_new_embedding_model("E5-base-v2") is True
        assert is_new_embedding_model("DistilBERT (Week 3)") is False
        assert is_new_embedding_model("Semantic Ensemble") is True
