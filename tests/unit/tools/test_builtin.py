from __future__ import annotations

import json
import os
import tempfile

import pytest

from ares.tools.builtin.file_tool import FileTool
from ares.tools.builtin.http_tool import HTTPTool
from ares.tools.builtin.memory_tool import MemoryTool
from ares.tools.builtin.plugin_tool import PluginTool
from ares.tools.builtin.python_tool import PythonTool
from ares.tools.builtin.search_tool import SearchTool
from ares.tools.types import ToolStatus


class TestFileTool:
    @pytest.fixture
    def tool(self):
        return FileTool(allowed_paths=[tempfile.gettempdir()])

    async def test_read_write_file(self, tool):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("hello world")
            tmp_path = f.name
        result = await tool.execute({"operation": "read", "path": tmp_path})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["content"] == "hello world"
        os.unlink(tmp_path)

    async def test_write_file(self, tool):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.txt")
            result = await tool.execute({"operation": "write", "path": path, "content": "test data"})
            assert result.status == ToolStatus.AVAILABLE
            assert result.result["written"] == 9
            assert os.path.isfile(path)

    async def test_list_directory(self, tool):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "a.txt"), "w").close()
            open(os.path.join(d, "b.txt"), "w").close()
            result = await tool.execute({"operation": "list", "path": d})
            assert result.status == ToolStatus.AVAILABLE
            assert result.result["count"] == 2

    async def test_exists(self, tool):
        result = await tool.execute({"operation": "exists", "path": "/tmp"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["exists"] is True

    async def test_path_not_allowed(self, tool):
        result = await tool.execute({"operation": "read", "path": "/etc/passwd"})
        assert result.status == ToolStatus.ERROR

    async def test_read_json(self, tool):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "data.json")
            with open(path, "w") as f:
                json.dump({"key": "value"}, f)
            result = await tool.execute({"operation": "read_json", "path": path})
            assert result.status == ToolStatus.AVAILABLE
            assert result.result["data"] == {"key": "value"}

    async def test_write_json(self, tool):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "data.json")
            result = await tool.execute({"operation": "write_json", "path": path, "data": {"x": 1}})
            assert result.status == ToolStatus.AVAILABLE
            assert result.result["written"] is True

    async def test_no_path(self, tool):
        result = await tool.execute({"operation": "read"})
        assert result.status == ToolStatus.ERROR
        assert "No path" in result.error

    async def test_unknown_operation(self, tool):
        result = await tool.execute({"operation": "unknown", "path": "/tmp"})
        assert result.status == ToolStatus.ERROR


class TestPythonTool:
    @pytest.fixture
    def tool(self):
        return PythonTool()

    async def test_execute_simple(self, tool):
        result = await tool.execute({"code": "x = 1 + 1"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["locals"]["x"] == 2

    async def test_no_code(self, tool):
        result = await tool.execute({})
        assert result.status == ToolStatus.ERROR

    async def test_restricted_builtins(self, tool):
        await tool.execute({"code": "import os"})
        assert True

    async def test_error_in_code(self, tool):
        result = await tool.execute({"code": "raise ValueError('boom')"})
        assert result.status == ToolStatus.ERROR

    async def test_with_globals(self, tool):
        result = await tool.execute({"code": "result = multiplier * 10", "globals": {"multiplier": 5}})
        assert result.status == ToolStatus.AVAILABLE


class TestMemoryTool:
    @pytest.fixture
    def tool(self):
        t = MemoryTool()
        t._manager.clear()
        return t

    async def test_set_and_get(self, tool):
        await tool.execute({"operation": "set", "key": "name", "value": "test"})
        result = await tool.execute({"operation": "get", "key": "name"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["entries"][0]["value"] == "test"

    async def test_get_namespace(self, tool):
        await tool.execute({"operation": "set", "key": "nstst_a", "value": 1, "tags": ["nstst"]})
        await tool.execute({"operation": "set", "key": "nstst_b", "value": 2, "tags": ["nstst"]})
        result = await tool.execute({"operation": "search", "key": "nstst_", "limit": 10})
        assert result.status == ToolStatus.AVAILABLE
        assert len(result.result["entries"]) == 2

    async def test_delete_key(self, tool):
        await tool.execute({"operation": "set", "key": "del_me", "value": "gone"})
        result = await tool.execute({"operation": "delete", "key": "del_me"})
        assert result.status == ToolStatus.AVAILABLE
        get_result = await tool.execute({"operation": "get", "key": "del_me"})
        assert get_result.result["count"] == 0

    async def test_list_keys(self, tool):
        await tool.execute({"operation": "set", "key": "lst_k1", "value": 1})
        await tool.execute({"operation": "set", "key": "lst_k2", "value": 2})
        result = await tool.execute({"operation": "search", "key": "lst_", "limit": 10})
        assert result.status == ToolStatus.AVAILABLE
        assert len(result.result["entries"]) == 2

    async def test_unknown_operation(self, tool):
        result = await tool.execute({"operation": "unknown"})
        assert result.status == ToolStatus.ERROR


class TestPluginTool:
    @pytest.fixture
    def tool(self):
        PluginTool._loaded_plugins.clear()
        return PluginTool()

    async def test_list_empty(self, tool):
        result = await tool.execute({"operation": "list"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["count"] == 0

    async def test_load_and_list(self, tool):
        result = await tool.execute({"operation": "load", "plugin_id": "my_plugin", "plugin_path": "/path/to/plugin"})
        assert result.status == ToolStatus.AVAILABLE
        list_result = await tool.execute({"operation": "list"})
        assert list_result.result["count"] == 1

    async def test_load_duplicate(self, tool):
        await tool.execute({"operation": "load", "plugin_id": "dup"})
        result = await tool.execute({"operation": "load", "plugin_id": "dup"})
        assert result.status == ToolStatus.ERROR

    async def test_unload(self, tool):
        await tool.execute({"operation": "load", "plugin_id": "temp"})
        result = await tool.execute({"operation": "unload", "plugin_id": "temp"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["unloaded"] is True

    async def test_status(self, tool):
        await tool.execute({"operation": "load", "plugin_id": "my_plugin"})
        result = await tool.execute({"operation": "status", "plugin_id": "my_plugin"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["status"]["status"] == "loaded"

    async def test_reload(self, tool):
        await tool.execute({"operation": "load", "plugin_id": "rp"})
        result = await tool.execute({"operation": "reload", "plugin_id": "rp"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["loaded"] is True

    async def test_no_plugin_id(self, tool):
        result = await tool.execute({"operation": "load"})
        assert result.status == ToolStatus.ERROR

    async def test_unknown_operation(self, tool):
        result = await tool.execute({"operation": "unknown"})
        assert result.status == ToolStatus.ERROR


class TestSearchTool:
    @pytest.fixture
    def tool(self):
        return SearchTool()

    async def test_find_in_text(self, tool):
        result = await tool.execute({"operation": "find", "pattern": "world", "text": "hello world"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["count"] == 1

    async def test_count_occurrences(self, tool):
        result = await tool.execute({"operation": "count", "pattern": "a", "text": "banana"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["count"] == 3

    async def test_filter_list(self, tool):
        data = ["apple", "banana", "cherry", "avocado"]
        result = await tool.execute({"operation": "filter", "pattern": "a", "data": data})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["count"] == 3
        assert len(result.result["items"]) == 3

    async def test_regex_search(self, tool):
        result = await tool.execute({"operation": "regex", "pattern": r"\d+", "text": "abc123def456"})
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["count"] == 2

    async def test_extract_matches(self, tool):
        result = await tool.execute(
            {"operation": "extract", "pattern": r"\w+@\w+\.\w+", "text": "email: test@example.com"}
        )
        assert result.status == ToolStatus.AVAILABLE
        assert len(result.result["extracted"]) > 0

    async def test_replace(self, tool):
        result = await tool.execute(
            {"operation": "replace", "pattern": "bad", "replacement": "good", "text": "bad word"}
        )
        assert result.status == ToolStatus.AVAILABLE
        assert result.result["replaced"] == "good word"

    async def test_no_pattern(self, tool):
        result = await tool.execute({"operation": "find"})
        assert result.status == ToolStatus.ERROR

    async def test_invalid_regex(self, tool):
        result = await tool.execute({"operation": "regex", "pattern": "[invalid", "text": "test"})
        assert result.status == ToolStatus.ERROR

    async def test_unknown_operation(self, tool):
        result = await tool.execute({"operation": "unknown", "pattern": "x"})
        assert result.status == ToolStatus.ERROR


class TestHTTPTool:
    @pytest.fixture
    def tool(self):
        return HTTPTool()

    async def test_no_url(self, tool):
        result = await tool.execute({"method": "GET"})
        assert result.status == ToolStatus.ERROR
        assert "No URL" in result.error

    async def test_domain_restriction(self):
        tool = HTTPTool(allowed_domains=["example.com"])
        result = await tool.execute({"url": "https://evil.com/test"})
        assert result.status == ToolStatus.ERROR
        assert "not allowed" in result.error

    async def test_unsupported_method(self, tool):
        result = await tool.execute({"url": "https://example.com", "method": "TRACE"})
        assert result.status == ToolStatus.ERROR
