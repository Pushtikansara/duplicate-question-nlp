from __future__ import annotations

from ares.query_understanding.complexity_models import ComplexityAnalysis


class ComplexityReport:
    def generate(self, analysis: ComplexityAnalysis, detailed: bool = True) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("COMPLEXITY ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"  Overall Complexity:  {analysis.overall_complexity_score:.4f}")
        lines.append(f"  Difficulty Level:     {analysis.difficulty_level}")
        lines.append(f"  Confidence Estimate:  {analysis.confidence_estimate:.4f}")
        lines.append(f"  Risk Score:           {analysis.risk_score:.4f}")
        lines.append(f"  Processing Time:      {analysis.processing_time:.2f} ms")
        lines.append(f"  Reasoning:            {analysis.reasoning_summary}")
        if detailed:
            lines.append("")
            lines.append("-" * 60)
            lines.append("DETAILED METRICS")
            lines.append("-" * 60)
            lines.append(f"  Lexical Complexity:       {analysis.lexical_complexity:.4f}")
            lines.append(f"  Syntactic Complexity:     {analysis.syntactic_complexity:.4f}")
            lines.append(f"  Semantic Complexity:      {analysis.semantic_complexity:.4f}")
            lines.append(f"  Entity Complexity:        {analysis.entity_complexity:.4f}")
            lines.append(f"  Ambiguity Score:          {analysis.ambiguity_score:.4f}")
            lines.append(f"  Readability Score:        {analysis.readability_score:.4f}")
            lines.append(f"  Comparison Difficulty:    {analysis.comparison_difficulty:.4f}")
            lines.append("")
            lines.append(f"  Rare Token Density:       {analysis.rare_token_density:.4f}")
            lines.append(f"  Entity Density:           {analysis.entity_density:.4f}")
            lines.append(f"  Numeric Density:          {analysis.numeric_density:.4f}")
            lines.append(f"  Abbreviation Density:     {analysis.abbreviation_density:.4f}")
            lines.append(f"  Sentence Complexity:      {analysis.sentence_complexity:.4f}")
            lines.append(f"  Question Length Score:    {analysis.question_length_score:.4f}")
            lines.append(f"  Token Diversity:          {analysis.token_diversity:.4f}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def short_report(self, analysis: ComplexityAnalysis) -> str:
        return (
            f"Complexity: {analysis.difficulty_level} "
            f"(score={analysis.overall_complexity_score:.4f}, "
            f"conf={analysis.confidence_estimate:.4f}, "
            f"risk={analysis.risk_score:.4f})"
        )
