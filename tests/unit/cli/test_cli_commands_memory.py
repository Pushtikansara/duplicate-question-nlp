from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ares.cli.app import app
from ares.cli.commands.memory import _get_memory_manager

runner = CliRunner()


class TestMemory:
    def test_get_memory_manager(self):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager"):
            mm = _get_memory_manager()
            assert mm is not None

    def test_list_memory(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search.return_value = [
                MagicMock(id="1", memory_type="episodic", timestamp=1000000, content="test content")
            ]
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "list"])
            assert result.exit_code == 0
            assert "Memory Entries" in result.output

    def test_list_memory_empty(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search.return_value = []
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "list"])
            assert "No memory entries found" in result.output

    def test_list_memory_by_type(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search_by_type.return_value = [
                MagicMock(id="1", memory_type="semantic", timestamp=1000000, content="data")
            ]
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "list", "--type", "semantic"])
            assert result.exit_code == 0
            assert "Memory Entries" in result.output

    def test_search_memory(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search_text.return_value = [MagicMock(id="1", timestamp=1000000, content="found it")]
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "search", "query"])
            assert result.exit_code == 0
            assert "Search results" in result.output

    def test_search_memory_no_results(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search_text.return_value = []
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "search", "nonexistent"])
            assert "No results" in result.output

    def test_search_memory_fallback(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.search_text.side_effect = Exception("fail")
            instance.search.return_value = [MagicMock(id="1", timestamp=1000000, content="found")]
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "search", "query"])
            assert result.exit_code == 0
            assert "Search results" in result.output

    def test_memory_stats(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.get_statistics.return_value = {
                "total_entries": 100,
                "memory_types": 5,
            }
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "stats"])
            assert result.exit_code == 0
            assert "Memory Statistics" in result.output
            assert "total_entries" in result.output

    def test_clean_memory_force(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.consolidate.return_value = "cleaned"
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "clean", "--force"])
            assert result.exit_code == 0
            assert "Memory cleaned" in result.output

    def test_clean_memory_by_type(self):
        with patch("ares.cli.commands.memory._get_memory_manager") as mock_mm:
            instance = MagicMock()
            instance.consolidate.return_value = "cleaned semantic"
            mock_mm.return_value = instance
            result = runner.invoke(app, ["memory", "clean", "--type", "semantic", "--force"])
            assert result.exit_code == 0
            instance.consolidate.assert_called_with("SEMANTIC")
