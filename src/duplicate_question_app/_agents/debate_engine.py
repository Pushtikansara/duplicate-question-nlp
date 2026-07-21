from __future__ import annotations

import time

from duplicate_question_app._agents.agent_registry import AgentRegistry
from duplicate_question_app._agents.agent_result import (
    AgentResult,
    AgreementMatrix,
    ConflictReport,
    ConsensusResult,
    DebateResult,
    Vote,
)
from duplicate_question_app._agents.conflict_resolution import DefaultConflictDetector
from duplicate_question_app._agents.consensus import DefaultConsensusStrategy
from duplicate_question_app._agents.interfaces import (
    ConflictDetectionStrategy,
    ConsensusStrategy,
)
from duplicate_question_app._reasoning.reasoning_result import ReasoningResult
from duplicate_question_app._semantic.representation import SemanticRepresentation
from duplicate_question_app._semantic_intelligence.semantic_assessment import SemanticAssessment


class DebateEngine:
    def __init__(
        self,
        registry: AgentRegistry | None = None,
        consensus_strategy: ConsensusStrategy | None = None,
        conflict_detector: ConflictDetectionStrategy | None = None,
    ):
        self._registry = registry or AgentRegistry()
        self._consensus = consensus_strategy or DefaultConsensusStrategy()
        self._conflict_detector = conflict_detector or DefaultConflictDetector()

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def consensus_strategy(self) -> ConsensusStrategy:
        return self._consensus

    @property
    def conflict_detector(self) -> ConflictDetectionStrategy:
        return self._conflict_detector

    def debate(
        self,
        rep_a: SemanticRepresentation,
        rep_b: SemanticRepresentation,
        assessment: SemanticAssessment | None = None,
        reasoning_result: ReasoningResult | None = None,
    ) -> DebateResult:
        start = time.perf_counter()
        stages: dict[str, float] = {}

        t0 = time.perf_counter()
        agents = self._registry.get_all()
        if not agents:
            return DebateResult(
                debate_summary="No agents registered",
                processing_time_ms=0.0,
            )
        t1 = time.perf_counter()
        stages["agent_loading"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        agent_results: list[AgentResult] = []
        for agent in agents:
            try:
                result = agent.evaluate(rep_a, rep_b, assessment, reasoning_result)
                agent_results.append(result)
            except Exception as exc:
                import logging

                logging.getLogger("duplicate_question_app._agents").error(
                    "Agent '%s' failed: %s", agent.name, exc, exc_info=True
                )
                agent_results.append(
                    AgentResult(
                        agent_name=agent.name,
                        confidence=0.0,
                        recommendation="uncertain",
                        warnings=[f"Agent evaluation failed: {exc}"],
                        metadata={"error": str(exc)},
                    )
                )
        t1 = time.perf_counter()
        stages["agent_evaluation"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        votes = self._build_votes(agent_results)
        t1 = time.perf_counter()
        stages["vote_building"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        plugins = self._registry.get_plugins()
        for plugin in plugins:
            try:
                plugin_results = plugin.process(rep_a, rep_b, assessment, reasoning_result, agent_results)
                if plugin_results:
                    existing_names = {r.agent_name for r in agent_results}
                    for pr in plugin_results:
                        if pr.agent_name not in existing_names:
                            agent_results.append(pr)
                            existing_names.add(pr.agent_name)
            except Exception as exc:
                import logging

                logging.getLogger("duplicate_question_app._agents").error(
                    "Plugin '%s' failed: %s", type(plugin).__name__, exc, exc_info=True
                )
        t1 = time.perf_counter()
        stages["plugin_processing"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        agreement_matrix = self._build_agreement_matrix(agent_results, votes)
        t1 = time.perf_counter()
        stages["agreement_matrix"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        conflict_reports = self._conflict_detector.detect(agent_results, votes)
        t1 = time.perf_counter()
        stages["conflict_detection"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        consensus = self._consensus.build(agent_results, votes, conflict_reports)
        t1 = time.perf_counter()
        stages["consensus"] = (t1 - t0) * 1000

        t0 = time.perf_counter()
        summary = self._build_summary(agent_results, votes, conflict_reports, consensus)
        t1 = time.perf_counter()
        stages["summary"] = (t1 - t0) * 1000

        total_time = (time.perf_counter() - start) * 1000

        return DebateResult(
            agent_results=agent_results,
            votes=votes,
            agreement_matrix=agreement_matrix,
            conflict_reports=conflict_reports,
            consensus=consensus,
            debate_summary=summary,
            processing_time_ms=total_time,
            stages=stages,
            agents_used=[a.agent_name for a in agent_results],
        )

    def _build_votes(self, results: list[AgentResult]) -> list[Vote]:
        votes: list[Vote] = []
        for r in results:
            if r.agent_name == "consensus_agent":
                continue
            weight = 1.0
            votes.append(
                Vote(
                    agent_name=r.agent_name,
                    recommendation=r.recommendation,
                    confidence=r.confidence,
                    weight=weight,
                )
            )
        return votes

    def _build_agreement_matrix(
        self,
        results: list[AgentResult],
        votes: list[Vote],
    ) -> AgreementMatrix:
        matrix: dict[str, dict[str, float]] = {}
        vote_map: dict[str, str] = {v.agent_name: v.recommendation for v in votes}
        agents = [r.agent_name for r in results if r.agent_name in vote_map]

        for a in agents:
            matrix[a] = {}
            for b in agents:
                if a == b:
                    matrix[a][b] = 1.0
                else:
                    ra = vote_map.get(a, "uncertain")
                    rb = vote_map.get(b, "uncertain")
                    matrix[a][b] = 1.0 if ra == rb else 0.0

        return AgreementMatrix(matrix=matrix)

    def _build_summary(
        self,
        results: list[AgentResult],
        votes: list[Vote],
        conflict_reports: list[ConflictReport],
        consensus: ConsensusResult | None,
    ) -> str:
        lines: list[str] = []
        lines.append("=== Multi-Agent Cognitive Debate Summary ===")
        lines.append(f"Total agents: {len(results)}")
        lines.append(f"Total conflicts: {len(conflict_reports)}")

        if votes:
            recs = {v.recommendation for v in votes}
            lines.append(f"Recommendations: {', '.join(sorted(recs))}")
            for rec in sorted(recs):
                rec_votes = [v for v in votes if v.recommendation == rec]
                if rec_votes:
                    avg_conf = sum(v.confidence for v in rec_votes) / len(rec_votes)
                    agents_str = ", ".join(v.agent_name for v in rec_votes)
                    lines.append(f"  {rec}: {len(rec_votes)} vote(s), avg confidence {avg_conf:.3f} [{agents_str}]")

        if conflict_reports:
            lines.append("\nConflicts:")
            for c in conflict_reports:
                lines.append(f"  [{c.conflict_type}] {c.description} (severity={c.severity:.2f})")

        if consensus:
            lines.append(f"\nConsensus: {consensus.decision} (confidence={consensus.confidence:.3f})")
            lines.append(f"Strategy: {consensus.strategy_used}")
            lines.append(f"Details: {consensus.details[:200]}")

        return "\n".join(lines)

    def set_consensus_strategy(self, strategy: ConsensusStrategy) -> None:
        self._consensus = strategy

    def set_conflict_detector(self, detector: ConflictDetectionStrategy) -> None:
        self._conflict_detector = detector
