from typing import Any

from duplicate_question_app._reflection.interfaces import ReflectionPlugin


class DefaultReflectionPlugin(ReflectionPlugin):
    def before_reflection(self, context: Any) -> Any:
        return context

    def after_reflection(self, result: Any) -> Any:
        return result

    def name(self) -> str:
        return "default"
