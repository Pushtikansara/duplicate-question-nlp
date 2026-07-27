from __future__ import annotations

from ares.query_understanding.router_models import RoutingDecision


class RouterReport:
    def generate(self, decision: RoutingDecision, detailed: bool = True) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("ROUTING DECISION REPORT")
        lines.append("=" * 60)
        lines.append(f"  Selected Strategy:  {decision.selected_strategy}")
        lines.append(f"  Confidence:         {decision.confidence:.4f}")
        lines.append(f"  Priority:           {decision.priority}")
        lines.append(f"  Risk Level:         {decision.risk_level}")
        lines.append(f"  Est. Cost:          {decision.estimated_cost:.2f}")
        lines.append(f"  Est. Latency:       {decision.estimated_latency:.1f} ms")
        lines.append(f"  Processing Time:    {decision.processing_time:.2f} ms")
        if decision.reason_codes:
            lines.append(f"  Reason Codes:       {', '.join(decision.reason_codes)}")
        if detailed:
            lines.append("")
            lines.append("-" * 60)
            lines.append("TRIGGERED RULES")
            lines.append("-" * 60)
            if decision.triggered_rules:
                for t in decision.triggered_rules:
                    lines.append(f"  [{t.get('category', '?')}] {t['rule']}")
                    lines.append(f"       {t['description']}")
                    lines.append(f"       score={t['score']}, weight={t['weight']}")
            else:
                lines.append("  No rules triggered")
            lines.append("")
            lines.append("-" * 60)
            lines.append("EXPLANATION")
            lines.append("-" * 60)
            lines.append(decision.explanation)
        lines.append("=" * 60)
        return "\n".join(lines)

    def short_report(self, decision: RoutingDecision) -> str:
        return (
            f"Route: {decision.selected_strategy} "
            f"(conf={decision.confidence:.4f}, "
            f"risk={decision.risk_level}, "
            f"latency={decision.estimated_latency:.1f}ms)"
        )
