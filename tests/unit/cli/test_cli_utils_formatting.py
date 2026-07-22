from __future__ import annotations

import json

import yaml

from ares.cli.utils.formatting import (
    checkmark,
    format_bytes,
    format_duration,
    format_percent,
    format_timestamp,
    output_result,
    save_output,
    status_tag,
    to_json,
    to_yaml,
    truncate,
)


class TestFormatting:
    def test_format_timestamp_none(self):
        assert format_timestamp(None) == "N/A"

    def test_format_timestamp_valid(self):
        result = format_timestamp(0)
        assert "1970" in result

    def test_format_duration_ms(self):
        assert "500.00ms" in format_duration(500)

    def test_format_duration_s(self):
        assert "1.50s" in format_duration(1500)

    def test_format_duration_m(self):
        assert "2.00m" in format_duration(120000)

    def test_format_bytes_b(self):
        assert "500.0B" in format_bytes(500)

    def test_format_bytes_kb(self):
        assert "1.5KB" in format_bytes(1536)

    def test_format_bytes_mb(self):
        assert "1.0MB" in format_bytes(1048576)

    def test_format_bytes_gb(self):
        result = format_bytes(1073741824)
        assert "GB" in result

    def test_format_bytes_tb(self):
        result = format_bytes(1099511627776)
        assert "TB" in result

    def test_format_percent(self):
        assert "50.0%" in format_percent(0.5)
        assert "100.0%" in format_percent(1.0)
        assert "0.0%" in format_percent(0.0)

    def test_truncate_short(self):
        assert truncate("hello") == "hello"

    def test_truncate_long(self):
        text = "a" * 100
        result = truncate(text, 10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_truncate_exact(self):
        text = "a" * 80
        assert truncate(text, 80) == text

    def test_to_json(self):
        data = {"key": "value", "num": 42}
        parsed = json.loads(to_json(data))
        assert parsed == data

    def test_to_json_with_dataclass(self):
        from dataclasses import dataclass

        @dataclass
        class Foo:
            x: int
            y: str

        result = to_json(Foo(1, "test"))
        assert "1" in result
        assert "test" in result

    def test_to_yaml(self):
        data = {"key": "value"}
        parsed = yaml.safe_load(to_yaml(data))
        assert parsed == data

    def test_output_result_json(self):
        data = {"a": 1}
        result = output_result(data, "json")
        parsed = json.loads(result)
        assert parsed == data

    def test_output_result_yaml(self):
        data = {"a": 1}
        result = output_result(data, "yaml")
        parsed = yaml.safe_load(result)
        assert parsed == data

    def test_output_result_text(self):
        assert output_result("hello", "text") == "hello"

    def test_output_result_text_from_dict(self):
        result = output_result({"a": 1}, "text")
        assert isinstance(result, str)

    def test_save_output(self, tmp_path):
        data = {"test": True}
        path = tmp_path / "output.json"
        result = save_output(data, path)
        assert result == path
        assert path.exists()
        parsed = json.loads(path.read_text())
        assert parsed == data

    def test_save_output_creates_dirs(self, tmp_path):
        data = {"test": True}
        path = tmp_path / "sub" / "nested" / "output.json"
        result = save_output(data, path)
        assert result.exists()

    def test_status_tag_pass(self):
        assert "PASS" in status_tag(True)

    def test_status_tag_fail(self):
        assert "FAIL" in status_tag(False)

    def test_checkmark_true(self):
        assert "\\u2713" in checkmark(True) or "\u2713" in checkmark(True)

    def test_checkmark_false(self):
        assert "\\u2717" in checkmark(False) or "\u2717" in checkmark(False)
