from __future__ import annotations

import json
from typing import Any

from ares.query_understanding.decision_trace_models import DecisionTrace


class DecisionTraceRenderer:
    def render_plaintext(self, trace: DecisionTrace) -> str:
        lines: list[str] = []
        lines.append("=" * 64)
        lines.append("DECISION TRACE")
        lines.append("=" * 64)
        lines.append(f"Pipeline Version: {trace.pipeline_version}")
        lines.append(f"Processing Time: {trace.processing_time_ms:.2f}ms")
        lines.append(f"Summary: {trace.summary}")
        lines.append(f"Overall Confidence: {trace.confidence:.4f}")
        lines.append(f"Overall Risk: {trace.overall_risk}")
        lines.append(f"Overall Complexity: {trace.overall_complexity}")
        lines.append("")

        lines.append("-" * 64)
        lines.append("DECISION PATH")
        lines.append("-" * 64)
        lines.append(f"Layers: {' -> '.join(trace.decision_path.layers_traversed)}")
        for step in trace.decision_path.decision_flow:
            lines.append(f"  -> {step}")
        lines.append("")

        lines.append("-" * 64)
        lines.append("QUESTION TYPE TRACE")
        lines.append("-" * 64)
        lines.append(f"  Q1 Type: {trace.question_type_trace.question_1_type}")
        lines.append(f"  Q2 Type: {trace.question_type_trace.question_2_type}")
        lines.append(f"  Pair Type: {trace.question_type_trace.pair_type}")
        lines.append(f"  Confidence: {trace.question_type_trace.confidence:.4f}")
        lines.append(f"  Reason: {trace.question_type_trace.reason}")
        lines.append("")

        lines.append("-" * 64)
        lines.append("ENTITY TRACE")
        lines.append("-" * 64)
        et = trace.entity_trace
        lines.append(f"  Q1 Entities: {et.entity_count_q1}, Q2 Entities: {et.entity_count_q2}")
        lines.append(f"  Shared: {et.shared_count}, Overlap: {et.overlap_score:.4f}")
        lines.append(f"  Relationship: {et.entity_relationship}")
        lines.append(f"  Confidence: {et.confidence:.4f}")
        for ev in et.evidence:
            tokens = ", ".join(ev.evidence_tokens)
            lines.append(f"  - [{ev.rule_name}] {ev.explanation} [{tokens}]")
        lines.append("")

        lines.append("-" * 64)
        lines.append("RELATIONSHIP TRACE")
        lines.append("-" * 64)
        rt = trace.relationship_trace
        lines.append(f"  Primary: {rt.primary_relationship}")
        lines.append(f"  Count: {rt.relationship_count}")
        lines.append(f"  Score: {rt.relationship_score:.2f}")
        lines.append(f"  Confidence: {rt.confidence:.4f}")
        if rt.semantic_flags:
            lines.append(f"  Semantic Flags: {', '.join(rt.semantic_flags)}")
        if rt.risk_flags:
            lines.append(f"  Risk Flags: {', '.join(rt.risk_flags)}")
        for ev in rt.evidence[:10]:  # limit display
            lines.append(f"  - [{ev.rule_name}] L{ev.rule_layer}: {ev.explanation}")
        if len(rt.evidence) > 10:
            lines.append(f"  ... and {len(rt.evidence) - 10} more evidence items")
        lines.append("")

        lines.append("-" * 64)
        lines.append("COMPLEXITY TRACE")
        lines.append("-" * 64)
        ct = trace.complexity_trace
        lines.append(f"  Overall: {ct.overall_score:.4f} ({ct.difficulty_level})")
        lines.append(f"  Lexical: {ct.lexical:.4f}, Syntactic: {ct.syntactic:.4f}, Semantic: {ct.semantic:.4f}")
        lines.append(f"  Entity: {ct.entity_complexity:.4f}, Ambiguity: {ct.ambiguity:.4f}")
        lines.append(f"  Readability: {ct.readability:.4f}, Comparison: {ct.comparison_difficulty:.4f}")
        lines.append(f"  Confidence: {ct.confidence:.4f}, Risk: {ct.risk_score:.4f}")
        lines.append(f"  Reasoning: {ct.reasoning}")
        lines.append("")

        lines.append("-" * 64)
        lines.append("ROUTING TRACE")
        lines.append("-" * 64)
        rout = trace.routing_trace
        lines.append(f"  Selected: {rout.selected_strategy}")
        lines.append(f"  Confidence: {rout.confidence:.4f}")
        lines.append(f"  Risk Level: {rout.risk_level}")
        lines.append(f"  Priority: {rout.priority}")
        lines.append("  Strategy Scores:")
        for strat, score in sorted(rout.strategy_scores.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"    {strat}: {score:.4f}")
        lines.append(f"  Triggered Rules: {len(rout.triggered_rules)}")
        for r in rout.triggered_rules:
            lines.append(f"    - {r.get('rule', '?')}: {r.get('description', '')} (score={r.get('score', 0):.4f})")
        if rout.rejected_rules:
            lines.append(f"  Rejected: {', '.join(rout.rejected_rules)}")
        lines.append("")

        lines.append("-" * 64)
        lines.append("CONFIDENCE BREAKDOWN")
        lines.append("-" * 64)
        cb = trace.confidence_breakdown
        lines.append(f"  Question Type: {cb.question_type:.4f}")
        lines.append(f"  Entity: {cb.entity:.4f}")
        lines.append(f"  Relationship: {cb.relationship:.4f}")
        lines.append(f"  Complexity: {cb.complexity:.4f}")
        lines.append(f"  Routing: {cb.routing:.4f}")
        lines.append(f"  Overall: {cb.overall:.4f}")
        lines.append("")

        if trace.warnings:
            lines.append("-" * 64)
            lines.append("WARNINGS")
            lines.append("-" * 64)
            for w in trace.warnings:
                lines.append(f"  ! {w}")
            lines.append("")

        if trace.recommendations:
            lines.append("-" * 64)
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 64)
            for r in trace.recommendations:
                lines.append(f"  * {r}")
            lines.append("")

        if trace.triggered_rules:
            lines.append("-" * 64)
            lines.append(f"ALL TRIGGERED RULES ({len(trace.triggered_rules)})")
            lines.append("-" * 64)
            for r in trace.triggered_rules:
                lines.append(f"  - {r}")
            lines.append("")

        lines.append("=" * 64)
        return "\n".join(lines)

    def render_markdown(self, trace: DecisionTrace) -> str:
        lines: list[str] = []
        lines.append("# Decision Trace")
        lines.append("")
        lines.append(f"- **Pipeline Version**: {trace.pipeline_version}")
        lines.append(f"- **Processing Time**: {trace.processing_time_ms:.2f}ms")
        lines.append(f"- **Summary**: {trace.summary}")
        lines.append(f"- **Overall Confidence**: {trace.confidence:.4f}")
        lines.append(f"- **Overall Risk**: {trace.overall_risk}")
        lines.append(f"- **Overall Complexity**: {trace.overall_complexity}")
        lines.append("")

        lines.append("## Decision Path")
        lines.append("")
        lines.append(f"**Layers**: {' → '.join(trace.decision_path.layers_traversed)}")
        lines.append("")
        for step in trace.decision_path.decision_flow:
            lines.append(f"- {step}")
        lines.append("")

        lines.append("## Question Type Trace")
        lines.append("")
        qt = trace.question_type_trace
        lines.append(f"- **Q1 Type**: {qt.question_1_type}")
        lines.append(f"- **Q2 Type**: {qt.question_2_type}")
        lines.append(f"- **Pair Type**: {qt.pair_type}")
        lines.append(f"- **Confidence**: {qt.confidence:.4f}")
        lines.append(f"- **Reason**: {qt.reason}")
        lines.append("")

        lines.append("## Entity Trace")
        lines.append("")
        et = trace.entity_trace
        lines.append(f"- **Q1 Entities**: {et.entity_count_q1}")
        lines.append(f"- **Q2 Entities**: {et.entity_count_q2}")
        lines.append(f"- **Shared**: {et.shared_count}")
        lines.append(f"- **Overlap Score**: {et.overlap_score:.4f}")
        lines.append(f"- **Entity Relationship**: {et.entity_relationship}")
        lines.append(f"- **Confidence**: {et.confidence:.4f}")
        for ev in et.evidence:
            tokens = ", ".join(ev.evidence_tokens)
            lines.append(f"- `{ev.rule_name}`: {ev.explanation} `[{tokens}]`")
        lines.append("")

        lines.append("## Relationship Trace")
        lines.append("")
        rt = trace.relationship_trace
        lines.append(f"- **Primary**: {rt.primary_relationship}")
        lines.append(f"- **Count**: {rt.relationship_count}")
        lines.append(f"- **Score**: {rt.relationship_score:.2f}")
        lines.append(f"- **Confidence**: {rt.confidence:.4f}")
        if rt.semantic_flags:
            lines.append(f"- **Semantic Flags**: {', '.join(rt.semantic_flags)}")
        if rt.risk_flags:
            lines.append(f"- **Risk Flags**: {', '.join(rt.risk_flags)}")
        for ev in rt.evidence[:10]:
            lines.append(f"- L{ev.rule_layer} `{ev.rule_name}`: {ev.explanation}")
        if len(rt.evidence) > 10:
            lines.append(f"- *... and {len(rt.evidence) - 10} more*")
        lines.append("")

        lines.append("## Complexity Trace")
        lines.append("")
        ct = trace.complexity_trace
        lines.append(f"- **Overall**: {ct.overall_score:.4f} ({ct.difficulty_level})")
        lines.append(
            f"- **Lexical**: {ct.lexical:.4f} | **Syntactic**: {ct.syntactic:.4f} | **Semantic**: {ct.semantic:.4f}"
        )
        lines.append(f"- **Entity**: {ct.entity_complexity:.4f} | **Ambiguity**: {ct.ambiguity:.4f}")
        lines.append(f"- **Readability**: {ct.readability:.4f} | **Comparison**: {ct.comparison_difficulty:.4f}")
        lines.append(f"- **Confidence**: {ct.confidence:.4f} | **Risk**: {ct.risk_score:.4f}")
        lines.append(f"- **Reasoning**: {ct.reasoning}")
        lines.append("")

        lines.append("## Routing Trace")
        lines.append("")
        rout = trace.routing_trace
        lines.append(f"- **Selected Strategy**: `{rout.selected_strategy}`")
        lines.append(f"- **Confidence**: {rout.confidence:.4f}")
        lines.append(f"- **Risk Level**: {rout.risk_level}")
        lines.append(f"- **Priority**: {rout.priority}")
        lines.append("- **Strategy Scores**:")
        for strat, score in sorted(rout.strategy_scores.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - `{strat}`: {score:.4f}")
        lines.append(f"- **Triggered Rules ({len(rout.triggered_rules)})**:")
        for r in rout.triggered_rules:
            lines.append(f"  - `{r.get('rule', '?')}`: {r.get('description', '')} (score={r.get('score', 0):.4f})")
        if rout.rejected_rules:
            lines.append(f"- **Rejected Strategies**: {', '.join(rout.rejected_rules)}")
        lines.append("")

        lines.append("## Confidence Breakdown")
        lines.append("")
        cb = trace.confidence_breakdown
        lines.append("| Stage | Confidence |")
        lines.append("|-------|------------|")
        lines.append(f"| Question Type | {cb.question_type:.4f} |")
        lines.append(f"| Entity | {cb.entity:.4f} |")
        lines.append(f"| Relationship | {cb.relationship:.4f} |")
        lines.append(f"| Complexity | {cb.complexity:.4f} |")
        lines.append(f"| Routing | {cb.routing:.4f} |")
        lines.append(f"| **Overall** | **{cb.overall:.4f}** |")
        lines.append("")

        if trace.warnings:
            lines.append("## Warnings")
            lines.append("")
            for w in trace.warnings:
                lines.append(f"- ⚠ {w}")
            lines.append("")

        if trace.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for r in trace.recommendations:
                lines.append(f"- {r}")
            lines.append("")

        return "\n".join(lines)

    def render_json(self, trace: DecisionTrace) -> str:
        return json.dumps(trace.to_dict(), indent=2, ensure_ascii=False)

    def render_dict(self, trace: DecisionTrace) -> dict[str, Any]:
        return trace.to_dict()
