from __future__ import annotations

import pytest

from duplicate_question_app._integration.compatibility import ModuleUnavailable, is_module_available


class TestModuleUnavailable:
    def test_available_false(self):
        mu = ModuleUnavailable("test")
        assert mu.available is False

    def test_method_call_raises(self):
        mu = ModuleUnavailable("test")
        with pytest.raises(RuntimeError, match="not available"):
            mu.some_method()


class TestIsModuleAvailable:
    def test_available_module(self):
        assert is_module_available("os") is True

    def test_unavailable_module(self):
        assert is_module_available("_nonexistent_module_xyz") is False
