from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IntegrationPlugin(ABC):
    @abstractmethod
    def before_pipeline(self, context: Any) -> Any: ...

    @abstractmethod
    def after_pipeline(self, result: Any) -> Any: ...


class DefaultIntegrationPlugin(IntegrationPlugin):
    def before_pipeline(self, context: Any) -> Any:
        return context

    def after_pipeline(self, result: Any) -> Any:
        return result
