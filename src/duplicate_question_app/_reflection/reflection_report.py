from __future__ import annotations

from datetime import datetime
from pathlib import Path

from duplicate_question_app._reflection.reflection_result import ReflectionResult


class ReflectionReportGenerator:
    def generate(self, results: list[ReflectionResult], output_dir: str | Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "reflection_report.md"
        with open(path, "w") as f:
            f.write("# ARES Reflection Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"Total predictions reflected: {len(results)}\n\n")
            trust_scores = [r.trust_score for r in results]
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
            f.write(f"Average Trust Score: {avg_trust:.2f}\n\n")
            reviews = sum(1 for r in results if r.human_review_required)
            f.write(f"Human Review Required: {reviews}/{len(results)}\n\n")
            f.write("## Per-Prediction Breakdown\n\n")
            for i, r in enumerate(results):
                f.write(f"### Prediction {i + 1}\n\n")
                f.write(f"- Trust Score: {r.trust_score:.1f} ({r.trust_level.value})\n")
                f.write(f"- Risk Level: {r.risk_level.value}\n")
                f.write(f"- Confidence: {r.confidence:.3f}\n")
                f.write(f"- Explainability: {r.explainability_score:.3f}\n")
                f.write(f"- Human Review: {'YES' if r.human_review_required else 'no'}\n")
                if r.human_review_required:
                    f.write(f"- Reason: {r.human_review_reason}\n")
                if r.recommendations:
                    f.write(f"- Recommendations: {', '.join(r.value for r in r.recommendations)}\n")
                if r.consistency_warnings:
                    f.write(f"- Warnings: {len(r.consistency_warnings)}\n")
                f.write("\n")
        return path
