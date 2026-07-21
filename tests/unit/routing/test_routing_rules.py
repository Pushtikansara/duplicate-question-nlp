from __future__ import annotations

from duplicate_question_app._routing.routing_context import RoutingContext
from duplicate_question_app._routing.routing_rules import RoutingRule, RoutingRulesEngine


class TestRoutingRule:
    def test_rule_creation(self):
        def condition(ctx: RoutingContext) -> bool:
            return True

        rule = RoutingRule(name="test", condition=condition, pipeline="full_cognitive", priority=10)
        assert rule.name == "test"
        assert rule.pipeline == "full_cognitive"
        assert rule.priority == 10

    def test_rule_evaluation_true(self):
        rule = RoutingRule(
            name="always_true",
            condition=lambda ctx: True,
            pipeline="uncertain_full",
            priority=5,
        )
        engine = RoutingRulesEngine(rules=[rule])
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 1
        assert matched[0].name == "always_true"

    def test_rule_evaluation_false(self):
        rule = RoutingRule(
            name="always_false",
            condition=lambda ctx: False,
            pipeline="simple",
            priority=5,
        )
        engine = RoutingRulesEngine(rules=[rule])
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 0

    def test_priority_ordering(self):
        low = RoutingRule(name="low", condition=lambda ctx: True, pipeline="simple", priority=1)
        high = RoutingRule(name="high", condition=lambda ctx: True, pipeline="complex", priority=10)
        engine = RoutingRulesEngine(rules=[low, high])
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 2
        assert matched[0].name == "high"
        assert matched[1].name == "low"

    def test_no_matching_rules(self):
        engine = RoutingRulesEngine()
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 0

    def test_multiple_rules_match(self):
        rule_a = RoutingRule(name="a", condition=lambda ctx: True, pipeline="p1", priority=1)
        rule_b = RoutingRule(name="b", condition=lambda ctx: True, pipeline="p2", priority=2)
        engine = RoutingRulesEngine(rules=[rule_a, rule_b])
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 2

    def test_add_rule(self):
        engine = RoutingRulesEngine()
        engine.add_rule(RoutingRule(name="added", condition=lambda ctx: True, pipeline="p", priority=5))
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 1

    def test_rule_with_context_question_length(self):
        def long_questions(ctx: RoutingContext) -> bool:
            return len(ctx.question_a) > 50 or len(ctx.question_b) > 50

        rule = RoutingRule(name="long", condition=long_questions, pipeline="full_cognitive", priority=5)
        engine = RoutingRulesEngine(rules=[rule])
        short_ctx = RoutingContext(question_a="Hi", question_b="Hello")
        assert len(engine.evaluate(short_ctx)) == 0
        long_ctx = RoutingContext(
            question_a="What is the difference between Python 2 and Python 3 in terms of Unicode handling?",
            question_b="How does the migration from Python 2 to Python 3 affect existing codebases?",
        )
        assert len(engine.evaluate(long_ctx)) == 1

    def test_rule_with_cross_encoder_score(self):
        def low_score(ctx: RoutingContext) -> bool:
            return ctx.cross_encoder_score is not None and ctx.cross_encoder_score < 0.4

        rule = RoutingRule(name="low_score", condition=low_score, pipeline="uncertain_full", priority=10)
        engine = RoutingRulesEngine(rules=[rule])
        high_ctx = RoutingContext(question_a="Q1", question_b="Q2", cross_encoder_score=0.9)
        assert len(engine.evaluate(high_ctx)) == 0
        low_ctx = RoutingContext(question_a="Q1", question_b="Q2", cross_encoder_score=0.2)
        assert len(engine.evaluate(low_ctx)) == 1

    def test_rule_exception_handling(self):
        def broken(ctx: RoutingContext) -> bool:
            raise RuntimeError("broken")

        rule = RoutingRule(name="broken", condition=broken, pipeline="p", priority=5)
        engine = RoutingRulesEngine(rules=[rule])
        context = RoutingContext(question_a="Q1", question_b="Q2")
        matched = engine.evaluate(context)
        assert len(matched) == 0
