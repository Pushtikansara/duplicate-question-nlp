from __future__ import annotations

from rich.table import Table
from rich.tree import Tree

from ares.cli.utils.tables import create_table, create_tree, dict_table, print_table


class TestTables:
    def test_create_table(self):
        table = create_table("Test", ["A", "B"], [["1", "2"], ["3", "4"]])
        assert isinstance(table, Table)
        assert table.title == "Test"

    def test_create_table_with_styles(self):
        table = create_table("Test", ["A", "B"], [["1", "2"]], styles=["red", "blue"])
        assert isinstance(table, Table)

    def test_print_table(self, capsys):
        print_table("Test", ["A", "B"], [["1", "2"]])
        captured = capsys.readouterr()
        assert "A" in captured.out
        assert "1" in captured.out

    def test_print_table_with_styles(self, capsys):
        print_table("Test", ["A", "B"], [["1", "2"]], styles=["green", "yellow"])
        captured = capsys.readouterr()
        assert "A" in captured.out

    def test_dict_table(self):
        table = dict_table("Config", {"key1": "val1", "key2": "val2"})
        assert isinstance(table, Table)

    def test_dict_table_keys(self):
        table = dict_table("Test", {"a": 1, "b": 2})
        rendered = str(table)
        assert "a" in rendered
        assert "b" in rendered

    def test_create_tree(self):
        tree = create_tree("root")
        assert isinstance(tree, Tree)
        assert tree.label == "root"

    def test_create_tree_with_children(self):
        tree = create_tree("root", {"child1": "val1", "child2": {"grandchild": "deep"}})
        assert isinstance(tree, Tree)

    def test_create_tree_nested(self):
        tree = create_tree("root", {"a": {"b": {"c": "d"}}})
        assert isinstance(tree, Tree)

    def test_create_table_empty_rows(self):
        table = create_table("Empty", ["A"], [])
        assert isinstance(table, Table)
