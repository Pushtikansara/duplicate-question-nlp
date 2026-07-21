from duplicate_question_app._reflection.interfaces import ReflectionPlugin


class DefaultReflectionPlugin(ReflectionPlugin):
    def before_reflection(self, context: any) -> any:
        return context

    def after_reflection(self, result: any) -> any:
        return result

    def name(self) -> str:
        return "default"
