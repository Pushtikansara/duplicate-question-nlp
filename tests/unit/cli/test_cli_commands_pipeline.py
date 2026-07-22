from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app

runner = CliRunner()


class TestPipeline:
    def test_inspect_pipeline(self):
        with patch("duplicate_question_app._integration.integration_configuration.IntegrationConfig") as mock_cfg:
            instance = MagicMock()
            instance.enable_perception = True
            instance.enable_routing = True
            instance.enable_memory_read = True
            instance.enable_semantic = True
            instance.enable_reasoning = True
            instance.enable_debate = True
            instance.enable_decision = True
            instance.enable_memory_write = True
            mock_cfg.return_value = instance
            result = runner.invoke(app, ["pipeline", "inspect"])
            assert result.exit_code == 0
            assert "Pipeline Modules" in result.output
            assert "Perception" in result.output

    def test_graph_pipeline(self):
        result = runner.invoke(app, ["pipeline", "graph"])
        assert result.exit_code == 0
        assert "Pipeline Graph" in result.output
        assert "Perception" in result.output

    def test_graph_pipeline_with_output(self, tmp_path):
        out = tmp_path / "graph.json"
        result = runner.invoke(app, ["pipeline", "graph", "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 8

    def test_run_pipeline(self):
        with patch("duplicate_question_app._integration.cognitive_pipeline.CognitivePipeline") as mock_pipe:
            instance = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.prediction = "duplicate"
            mock_meta = MagicMock()
            mock_meta.total_latency_ms = 150
            mock_meta.modules_executed = 8
            mock_result.metadata = mock_meta
            instance.run.return_value = mock_result
            mock_pipe.return_value = instance
            result = runner.invoke(app, ["pipeline", "run", "q1", "q2"])
            assert result.exit_code == 0
            assert "Pipeline Result" in result.output

    def test_run_pipeline_with_output(self, tmp_path):
        with patch("duplicate_question_app._integration.cognitive_pipeline.CognitivePipeline") as mock_pipe:
            instance = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.prediction = "duplicate"
            mock_meta = MagicMock()
            mock_meta.total_latency_ms = 150
            mock_meta.modules_executed = 8
            mock_result.metadata = mock_meta
            instance.run.return_value = mock_result
            mock_pipe.return_value = instance
            out = tmp_path / "result.json"
            result = runner.invoke(app, ["pipeline", "run", "q1", "q2", "--output", str(out)])
            assert result.exit_code == 0
            assert out.exists()
            data = json.loads(out.read_text())
            assert data["success"] is True

    def test_run_pipeline_failure(self):
        with patch("duplicate_question_app._integration.cognitive_pipeline.CognitivePipeline") as mock_pipe:
            instance = MagicMock()
            instance.run.side_effect = Exception("boom")
            mock_pipe.return_value = instance
            result = runner.invoke(app, ["pipeline", "run", "q1", "q2"])
            assert result.exit_code != 0
