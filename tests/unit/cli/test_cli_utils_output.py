from __future__ import annotations

from ares.cli.utils.output import OutputFormat, OutputHandler


class TestOutputFormat:
    def test_text_value(self):
        assert OutputFormat.TEXT.value == "text"

    def test_json_value(self):
        assert OutputFormat.JSON.value == "json"

    def test_yaml_value(self):
        assert OutputFormat.YAML.value == "yaml"

    def test_from_string(self):
        assert OutputFormat("json") == OutputFormat.JSON
        assert OutputFormat("yaml") == OutputFormat.YAML
        assert OutputFormat("text") == OutputFormat.TEXT


class TestOutputHandler:
    def test_default_format(self):
        oh = OutputHandler()
        assert oh.format == OutputFormat.TEXT
        assert oh.is_text
        assert not oh.is_json
        assert not oh.is_yaml

    def test_json_format(self):
        oh = OutputHandler(format=OutputFormat.JSON)
        assert oh.is_json
        assert not oh.is_text
        assert not oh.is_yaml

    def test_yaml_format(self):
        oh = OutputHandler(format=OutputFormat.YAML)
        assert oh.is_yaml
        assert not oh.is_text
        assert not oh.is_json

    def test_quiet_suppresses_print(self, capsys):
        oh = OutputHandler(quiet=True)
        oh.print("hello")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_text(self, capsys):
        oh = OutputHandler()
        oh.print("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_print_json(self, capsys):
        oh = OutputHandler(format=OutputFormat.JSON)
        oh.print({"key": "val"})
        captured = capsys.readouterr()
        assert "key" in captured.out
        assert "val" in captured.out

    def test_print_with_file(self, tmp_path, capsys):
        oh = OutputHandler()
        f = tmp_path / "out.json"
        oh.print({"a": 1}, file=str(f))
        assert f.exists()

    def test_print_error(self, capsys):
        oh = OutputHandler()
        oh.print_error("err")
        captured = capsys.readouterr()
        assert "err" in captured.err

    def test_print_info_quiet(self, capsys):
        oh = OutputHandler(quiet=True)
        oh.print_info("info")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_info(self, capsys):
        oh = OutputHandler()
        oh.print_info("info msg")
        captured = capsys.readouterr()
        assert "info msg" in captured.out

    def test_print_success(self, capsys):
        oh = OutputHandler()
        oh.print_success("success")
        captured = capsys.readouterr()
        assert "success" in captured.out

    def test_print_table_text(self, capsys):
        oh = OutputHandler()
        oh.print_table("Test", ["A", "B"], [["1", "2"]])
        captured = capsys.readouterr()
        assert "A" in captured.out
        assert "1" in captured.out

    def test_print_table_json(self, capsys):
        oh = OutputHandler(format=OutputFormat.JSON)
        oh.print_table("Test", ["A", "B"], [["1", "2"]])
        captured = capsys.readouterr()
        assert "Test" in captured.out or "A" in captured.out

    def test_print_dict_text(self, capsys):
        oh = OutputHandler()
        oh.print_dict("Config", {"key": "val"})
        captured = capsys.readouterr()
        assert "key" in captured.out
        assert "val" in captured.out

    def test_print_dict_json(self, capsys):
        oh = OutputHandler(format=OutputFormat.JSON)
        oh.print_dict("Config", {"key": "val"})
        captured = capsys.readouterr()
        assert "key" in captured.out

    def test_output_handler_verbose(self):
        oh = OutputHandler(verbose=True)
        assert oh.verbose

    def test_output_handler_text_default(self):
        oh = OutputHandler()
        assert oh.format == OutputFormat.TEXT
