from __future__ import annotations

from ares.query_understanding.entity_models import EntityResult


class EntityReport:
    def generate_section(self, result: EntityResult) -> str:
        lines = []
        lines.append("  Entity Analysis")
        lines.append(f"    Relationship: {result.entity_relationship}")
        lines.append(f"    Overlap Score: {result.entity_overlap_score:.4f}")
        lines.append("")

        if result.entities_1:
            lines.append(f"    Q1 Entities ({len(result.entities_1)}):")
            for e in result.entities_1:
                lines.append(f"      [{e.entity_type:22}] {e.text}")
        else:
            lines.append("    Q1 Entities: none")

        lines.append("")

        if result.entities_2:
            lines.append(f"    Q2 Entities ({len(result.entities_2)}):")
            for e in result.entities_2:
                lines.append(f"      [{e.entity_type:22}] {e.text}")
        else:
            lines.append("    Q2 Entities: none")

        lines.append("")

        if result.shared_entities:
            lines.append(f"    Shared Entities ({len(result.shared_entities)}):")
            for m in result.shared_entities:
                lines.append(
                    f"      [{m.match_type:18}] {m.entity_1.text} ↔ {m.entity_2.text} (sim={m.similarity:.2f})"
                )
        else:
            lines.append("    Shared Entities: none")

        lines.append("")

        if result.unique_entities_q1:
            lines.append(f"    Unique to Q1 ({len(result.unique_entities_q1)}):")
            for e in result.unique_entities_q1:
                lines.append(f"      [{e.entity_type:22}] {e.text}")
            lines.append("")

        if result.unique_entities_q2:
            lines.append(f"    Unique to Q2 ({len(result.unique_entities_q2)}):")
            for e in result.unique_entities_q2:
                lines.append(f"      [{e.entity_type:22}] {e.text}")
            lines.append("")

        return "\n".join(lines)

    def generate_short(self, result: EntityResult) -> str:
        parts = []
        if result.entity_relationship != "no_entities":
            parts.append(f"Entities: {result.entity_relationship}")
            e1_count = len(result.entities_1)
            e2_count = len(result.entities_2)
            shared_count = len(result.shared_entities)
            parts.append(f"  Q1:{e1_count} Q2:{e2_count} Shared:{shared_count}")
        return "\n".join(parts)

    def entity_type_summary(self, result: EntityResult) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in result.entities_1 + result.entities_2:
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))
