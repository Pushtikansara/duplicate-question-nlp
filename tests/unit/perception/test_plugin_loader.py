"""Tests for the Plugin Loader."""

from __future__ import annotations

import tempfile

import pytest

from duplicate_question_app._perception.exceptions import PluginLoadError
from duplicate_question_app._perception.plugin_loader import DefaultPluginLoader


class TestDefaultPluginLoader:
    def test_load_nonexistent_module_raises(self):
        loader = DefaultPluginLoader()
        with pytest.raises(PluginLoadError):
            loader.load_plugin("nonexistent_module_xyz")

    def test_discover_nonexistent_directory_raises(self):
        loader = DefaultPluginLoader()
        with pytest.raises(PluginLoadError):
            loader.discover_plugins("/nonexistent/path")

    def test_discover_empty_directory(self):
        loader = DefaultPluginLoader()
        with tempfile.TemporaryDirectory() as tmpdir:
            plugins = loader.discover_plugins(tmpdir)
            assert plugins == []

    def test_get_loaded_plugins_initially_empty(self):
        loader = DefaultPluginLoader()
        assert loader.get_loaded_plugins() == {}
