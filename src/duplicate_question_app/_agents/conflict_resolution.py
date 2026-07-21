from __future__ import annotations

from collections import Counter

from duplicate_question_app._agents.agent_result import AgentResult, ConflictReport, Vote
from duplicate_question_app._agents.interfaces import ConflictDetectionStrategy


class DefaultConflictDetector(ConflictDetectionStrategy):
    def detect(
        self,
        results: list[AgentResult],
        votes: list[Vote],
    ) -> list[ConflictReport]:
        reports: list[ConflictReport] = []

        vote_map: dict[str, str] = {v.agent_name: v.recommendation for v in votes}
        confidence_map: dict[str, float] = {r.agent_name: r.confidence for r in results}

        recommendations = list(vote_map.values())
        rec_counts: Counter[str] = Counter(recommendations)
        if len(rec_counts) >= 2:
            minority_recs = [r for r in recommendations if r != rec_counts.most_common(1)[0][0]]
            minority_agents = [name for name, rec in vote_map.items() if rec in minority_recs]
            if minority_agents:
                reports.append(
                    ConflictReport(
                        conflict_type="agent_disagreement",
                        agents=minority_agents,
                        description=f"Agents disagree with majority: {', '.join(minority_agents)}",
                        severity=len(minority_agents) / max(1, len(votes)),
                    )
                )

        low_conf_agents = [name for name, conf in confidence_map.items() if conf < 0.4]
        if low_conf_agents:
            reports.append(
                ConflictReport(
                    conflict_type="low_confidence",
                    agents=low_conf_agents,
                    description=f"Agents with low confidence (< 0.4): {', '.join(low_conf_agents)}",
                    severity=0.3,
                )
            )

        opposite_pairs = self._find_opposite_conclusions(vote_map)
        for a, b in opposite_pairs:
            reports.append(
                ConflictReport(
                    conflict_type="opposite_conclusion",
                    agents=[a, b],
                    description=f"Agent '{a}' and '{b}' reached opposite conclusions",
                    severity=0.8,
                )
            )

        for r in results:
            if not r.supporting_evidence and not r.contradicting_evidence:
                reports.append(
                    ConflictReport(
                        conflict_type="missing_evidence",
                        agents=[r.agent_name],
                        description=f"Agent '{r.agent_name}' produced no evidence",
                        severity=0.4,
                    )
                )

            has_contra = len(r.contradicting_evidence) > 0
            has_support = len(r.supporting_evidence) > 0
            if has_contra and has_support:
                reports.append(
                    ConflictReport(
                        conflict_type="contradictory_evidence",
                        agents=[r.agent_name],
                        description=f"Agent '{r.agent_name}' has both supporting and contradicting evidence",
                        severity=min(
                            1.0,
                            len(r.contradicting_evidence)
                            / max(1, len(r.supporting_evidence) + len(r.contradicting_evidence)),
                        ),
                    )
                )

        for r in results:
            warnings_seen = len(r.warnings)
            if warnings_seen > 0:
                reports.append(
                    ConflictReport(
                        conflict_type="agent_warnings",
                        agents=[r.agent_name],
                        description=f"Agent '{r.agent_name}' raised {warnings_seen} warning(s)",
                        severity=min(0.5, warnings_seen * 0.1),
                    )
                )

        return reports

    def _find_opposite_conclusions(self, vote_map: dict[str, str]) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        agents = list(vote_map.keys())
        opposite_map = {"duplicate": "not_duplicate", "not_duplicate": "duplicate"}
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a, b = agents[i], agents[j]
                ra, rb = vote_map.get(a), vote_map.get(b)
                if ra and rb and opposite_map.get(ra) == rb:
                    pairs.append((a, b))
        return pairs
