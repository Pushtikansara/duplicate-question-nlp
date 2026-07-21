from __future__ import annotations

from duplicate_question_app._agents.agent_result import AgentResult
from duplicate_question_app._agents.interfaces import AgentPlugin
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class DefaultAgentPlugin(AgentPlugin):
    def process(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None,
        reasoning_result: ReasoningResult | None,
        agent_results: list[AgentResult],
    ) -> list[AgentResult]:
        return agent_results
