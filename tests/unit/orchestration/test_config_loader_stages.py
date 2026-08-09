from __future__ import annotations

from pathlib import Path

import pytest

from ares.orchestration.config_loader import build_pipeline_stage_config, load_orchestration_yaml
from ares.orchestration.exceptions import InvalidStageConfigurationError

CONFIGS_DIR = Path(__file__).resolve().parents[3] / "configs"


class TestPipelineStageConfig:
    def test_real_config_defines_five_stages_in_order(self):
        config = load_orchestration_yaml()
        stages = config["pipeline"]["stages"]
        assert list(stages) == [
            "InputValidationStage",
            "QueryUnderstandingStage",
            "StrategySelectionStage",
            "PredictionStage",
            "ResultEnrichmentStage",
        ]
        assert stages["InputValidationStage"]["order"] == 1
        assert stages["StrategySelectionStage"]["depends_on"] == ["QueryUnderstandingStage"]

    def test_build_pipeline_stage_config_from_real_config(self):
        stages = build_pipeline_stage_config()
        assert set(stages) == {
            "InputValidationStage",
            "QueryUnderstandingStage",
            "StrategySelectionStage",
            "PredictionStage",
            "ResultEnrichmentStage",
        }

    def test_missing_directory_returns_empty(self, tmp_path: Path):
        assert build_pipeline_stage_config(config_dir=tmp_path) == {}

    def test_custom_config_parsed(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text(
            "pipeline:\n  stages:\n    InputValidationStage:\n      enabled: false\n      order: 9\n"
        )
        stages = build_pipeline_stage_config(config_dir=tmp_path)
        assert stages == {"InputValidationStage": {"enabled": False, "order": 9}}

    def test_unknown_stage_rejected(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text("pipeline:\n  stages:\n    MysteryStage:\n      enabled: true\n")
        with pytest.raises(InvalidStageConfigurationError):
            build_pipeline_stage_config(config_dir=tmp_path)

    def test_non_mapping_stages_rejected(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text("pipeline:\n  stages: [1, 2]\n")
        with pytest.raises(InvalidStageConfigurationError):
            build_pipeline_stage_config(config_dir=tmp_path)

    def test_unsupported_key_rejected(self, tmp_path: Path):
        (tmp_path / "orchestration.yaml").write_text(
            "pipeline:\n  stages:\n    PredictionStage:\n      timeout_ms: 5000\n"
        )
        with pytest.raises(InvalidStageConfigurationError):
            build_pipeline_stage_config(config_dir=tmp_path)
