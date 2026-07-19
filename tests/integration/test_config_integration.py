from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from duplicate_question_app._config.loader import clear_config_cache, load_all_configs
from duplicate_question_app._config.settings import _reload_module_constants


class TestConfigIntegration:
    @pytest.mark.integration
    def test_full_config_loading_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            configs = {
                "app": {"default_model": "E5-base-v2", "default_threshold": 0.5, "default_device": "cpu"},
                "paths": {"data_dir": "data", "models_dir": "models"},
                "models": {"model_choices": ["E5-base-v2", "BGE-base-en-v1.5"]},
                "inference": {"default_threshold": 0.5, "batch_size": 32},
                "training": {"seed": 42, "splits": {"train": 0.8, "val": 0.1, "test": 0.1}},
                "evaluation": {"ece_bins": 15},
                "dataset": {"train_file": "train.parquet"},
                "logging": {"level": "INFO"},
            }
            for name, cfg in configs.items():
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump(cfg, f)

            clear_config_cache()
            loaded = load_all_configs(config_dir=config_dir)

            assert loaded["app"]["default_model"] == "E5-base-v2"
            assert loaded["inference"]["batch_size"] == 32
            assert loaded["training"]["seed"] == 42

    @pytest.mark.integration
    def test_config_with_env_overrides_integration(self):
        os.environ["DQD_DEFAULT_MODEL"] = "env-override-model"
        os.environ["DQD_DEFAULT_THRESHOLD"] = "0.75"

        clear_config_cache()
        _reload_module_constants()
        try:
            loaded = load_all_configs()
            assert loaded["app"]["default_model"] == "env-override-model"
            assert loaded["inference"]["default_threshold"] == 0.75
        finally:
            os.environ.pop("DQD_DEFAULT_MODEL", None)
            os.environ.pop("DQD_DEFAULT_THRESHOLD", None)

    @pytest.mark.integration
    def test_config_with_local_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            base_cfg = {"default_model": "base-model", "default_threshold": 0.5}
            local_cfg = {"default_model": "local-model"}

            with open(config_dir / "app.yaml", "w") as f:
                yaml.dump(base_cfg, f)
            for name in ["paths", "models", "inference", "training", "evaluation", "dataset", "logging"]:
                with open(config_dir / f"{name}.yaml", "w") as f:
                    yaml.dump({}, f)
            with open(config_dir / "local.yaml", "w") as f:
                yaml.dump({"app": local_cfg}, f)

            clear_config_cache()
            loaded = load_all_configs(config_dir=config_dir)
            assert loaded["app"]["default_model"] == "local-model"
            assert loaded["app"]["default_threshold"] == 0.5

    @pytest.mark.integration
    def test_config_cache_invalidation(self):
        clear_config_cache()
        cfg1 = load_all_configs()
        clear_config_cache()
        cfg2 = load_all_configs()
        assert cfg1 is not cfg2
        assert cfg1.keys() == cfg2.keys()

    @pytest.mark.integration
    def test_multiple_get_config_calls_consistent(self):
        from duplicate_question_app._config.loader import get_config
        clear_config_cache()
        c1 = get_config("app")
        c2 = get_config("app")
        assert c1 == c2
        assert c1 is c2
