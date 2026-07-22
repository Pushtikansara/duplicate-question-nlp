from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.trace import (
    _get_trace_recorder,
    _to_chrome_trace,
)

runner = CliRunner()


class TestTrace:
    def test_run_trace(self):
        with patch("duplicate_question_app._explainability.trace.generate_decision_trace") as mock_gen:
            mock_trace = MagicMock()
            mock_trace.to_dict.return_value = {"decision": "test"}
            mock_gen.return_value = mock_trace
            result = runner.invoke(app, ["trace", "run", "q1", "q2"])
            assert result.exit_code == 0
            assert "decision" in result.output

    def test_run_trace_with_output(self, tmp_path):
        out = tmp_path / "trace.json"
        with patch("duplicate_question_app._explainability.trace.generate_decision_trace") as mock_gen:
            mock_trace = MagicMock()
            mock_trace.to_dict.return_value = {"decision": "test"}
            mock_gen.return_value = mock_trace
            result = runner.invoke(app, ["trace", "run", "q1", "q2", "--output", str(out)])
            assert result.exit_code == 0
            assert out.exists()
            assert "Trace saved" in result.output

    def test_run_trace_failure(self):
        with patch(
            "duplicate_question_app._explainability.trace.generate_decision_trace",
            side_effect=Exception("fail"),
        ):
            result = runner.invoke(app, ["trace", "run", "q1", "q2"])
            assert result.exit_code != 0

    def test_inspect_trace(self, tmp_path):
        f = tmp_path / "trace.json"
        f.write_text(json.dumps({"key": "val", "nested": {"inner": "deep"}, "items": [1, 2]}))
        result = runner.invoke(app, ["trace", "inspect", str(f)])
        assert result.exit_code == 0
        assert "Trace Details" in result.output
        assert "key" in result.output
        assert "val" in result.output

    def test_inspect_trace_not_found(self):
        result = runner.invoke(app, ["trace", "inspect", "/nonexistent/trace.json"])
        assert result.exit_code != 0

    def test_inspect_trace_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json")
        result = runner.invoke(app, ["trace", "inspect", str(f)])
        assert result.exit_code != 0

    def test_export_trace(self, tmp_path):
        src = tmp_path / "trace.json"
        src.write_text(json.dumps({"key": "val"}))
        dst = tmp_path / "export.json"
        result = runner.invoke(app, ["trace", "export", str(src), str(dst)])
        assert result.exit_code == 0
        assert dst.exists()
        parsed = json.loads(dst.read_text())
        assert parsed == {"key": "val"}

    def test_export_trace_chrome(self, tmp_path):
        src = tmp_path / "trace.json"
        src.write_text(json.dumps({"key": "val"}))
        dst = tmp_path / "chrome.json"
        result = runner.invoke(app, ["trace", "export", str(src), str(dst), "--format", "chrome"])
        assert result.exit_code == 0
        assert dst.exists()
        parsed = json.loads(dst.read_text())
        assert isinstance(parsed, list)

    def test_export_trace_not_found(self):
        result = runner.invoke(app, ["trace", "export", "/nonexistent.json", "/out.json"])
        assert result.exit_code != 0

    def test_export_trace_bad_format(self, tmp_path):
        src = tmp_path / "trace.json"
        src.write_text(json.dumps({"key": "val"}))
        result = runner.invoke(app, ["trace", "export", str(src), "/out.json", "--format", "xml"])
        assert result.exit_code != 0

    def test_to_chrome_trace(self):
        events = _to_chrome_trace({"func1": "val1", "func2": "val2"})
        assert len(events) == 2
        assert events[0]["name"] == "func1"
        assert events[0]["ph"] == "i"

    def test_replay_trace(self, tmp_path):
        f = tmp_path / "trace.json"
        f.write_text(json.dumps({"key": "val"}))
        result = runner.invoke(app, ["trace", "replay", str(f)])
        assert result.exit_code == 0
        assert "Replaying trace" in result.output
        assert "Trace replay complete" in result.output

    def test_replay_trace_not_found(self):
        result = runner.invoke(app, ["trace", "replay", "/nonexistent.json"])
        assert result.exit_code != 0

    def test_get_trace_recorder(self):
        with patch("duplicate_question_app._reasoning.reasoning_trace.TraceRecorder"):
            recorder = _get_trace_recorder()
            assert recorder is not None
