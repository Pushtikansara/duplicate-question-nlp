from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EvaluationPlugin(ABC):
    @abstractmethod
    def before_evaluation(self, config: Any) -> Any: ...

    @abstractmethod
    def after_evaluation(self, results: list[Any]) -> Any: ...

    @abstractmethod
    def name(self) -> str: ...


class DefaultEvaluationPlugin(EvaluationPlugin):
    def before_evaluation(self, config: Any) -> Any:
        return config

    def after_evaluation(self, results: list[Any]) -> list[Any]:
        return results

    def name(self) -> str:
        return "default"
