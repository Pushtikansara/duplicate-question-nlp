from __future__ import annotations

from typing import Any


class ModuleUnavailable:
    def __init__(self, module_name: str) -> None:
        self._name = module_name

    def __getattr__(self, name: str) -> Any:
        return _unavailable_stub

    @property
    def available(self) -> bool:
        return False


def _unavailable_stub(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError("Module is not available")


def is_module_available(module_path: str) -> bool:
    try:
        __import__(module_path, fromlist=[""])
        return True
    except ImportError:
        return False
