from __future__ import annotations

from ares.query_understanding.relationship_models import RelationshipAnalysis


class RelationshipReport:
    def generate(self, analysis: RelationshipAnalysis) -> str:
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("RELATIONSHIP ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")

        lines.append(f"Primary Relationship: {analysis.primary_relationship().replace('_', ' ').title()}")
        lines.append(f"Relationship Score: {analysis.relationship_score}/100")
        lines.append(f"Confidence: {analysis.relationship_confidence}")
        lines.append(f"Risk Score: {analysis.risk_score()}/100")
        lines.append(f"Semantic Distance: {analysis.semantic_distance()}/100")
        lines.append(f"Summary: {analysis.relationship_summary}")
        lines.append(f"Processing Time: {analysis.processing_time}ms")
        lines.append(f"Version: {analysis.version}")
        lines.append("")

        if analysis.relationship_types:
            lines.append("-" * 40)
            lines.append("DETECTED RELATIONSHIPS")
            lines.append("-" * 40)
            for rel in sorted(analysis.relationship_types, key=lambda r: r.confidence, reverse=True):
                rtype = rel.relationship_type.replace("_", " ").title()
                lines.append(f"  {rtype}: {rel.confidence:.2f}")
                if rel.human_explanation:
                    lines.append(f"    {rel.human_explanation}")
                for ev in rel.evidence:
                    if ev.tokens_q1 or ev.tokens_q2:
                        t1 = ", ".join(ev.tokens_q1)
                        t2 = ", ".join(ev.tokens_q2)
                        lines.append(f"    Evidence: [{t1}] -> [{t2}]")
            lines.append("")

        if analysis.semantic_flags:
            lines.append("-" * 40)
            lines.append("SEMANTIC FLAGS")
            lines.append("-" * 40)
            for flag in analysis.semantic_flags:
                lines.append(f"  {flag.replace('_', ' ').title()}")
            lines.append("")

        if analysis.risk_flags:
            lines.append("-" * 40)
            lines.append("RISK FLAGS")
            lines.append("-" * 40)
            for flag in analysis.risk_flags:
                lines.append(f"  {flag.replace('_', ' ').title()}")
            lines.append("")

        if analysis.transformation_chain.steps:
            lines.append("-" * 40)
            lines.append("TRANSFORMATION CHAIN")
            lines.append("-" * 40)
            for i, step in enumerate(analysis.transformation_chain.steps, 1):
                stype = step.step_type.replace("_", " ").title()
                lines.append(f"  {i}. {stype} (conf: {step.confidence:.2f})")
                if step.description:
                    lines.append(f"     {step.description}")
            lines.append(f"  Final Intent: {analysis.transformation_chain.final_intent}")
            lines.append(f"  Equivalent: {analysis.transformation_chain.is_equivalent}")
            lines.append("")

        cs = analysis.comparison_statistics
        lines.append("-" * 40)
        lines.append("COMPARISON STATISTICS")
        lines.append("-" * 40)
        lines.append(f"  Token Count: Q1={cs.token_count_q1}, Q2={cs.token_count_q2}")
        lines.append(f"  Char Count: Q1={cs.char_count_q1}, Q2={cs.char_count_q2}")
        lines.append(f"  Token Overlap: {cs.token_overlap} ({cs.token_overlap_ratio:.1%})")
        lines.append(f"  Edit Distance: {cs.edit_distance}")
        lines.append(f"  Normalized Edit Distance: {cs.normalized_edit_distance:.4f}")
        lines.append(f"  Jaccard Similarity: {cs.jaccard_similarity:.4f}")
        lines.append(f"  Shared Token Ratio: {cs.shared_token_ratio:.2%}")
        lines.append("")

        return "\n".join(lines)

    def generate_developer(self, analysis: RelationshipAnalysis) -> str:
        import json

        return json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False)

    def generate_machine(self, analysis: RelationshipAnalysis) -> dict:
        return analysis.to_dict()
