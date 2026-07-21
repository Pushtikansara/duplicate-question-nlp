"""IntentMatcher — compares semantic intent between two SemanticRepresentations.

Produces a match score, confidence, and human-readable reason.
"""

from __future__ import annotations

from duplicate_question_app._semantic.representation import SemanticRepresentation


class DefaultIntentMatcher:
    def match(self, rep_a: SemanticRepresentation, rep_b: SemanticRepresentation) -> dict:
        summary_a = (rep_a.intent_summary or "").lower().strip()
        summary_b = (rep_b.intent_summary or "").lower().strip()

        actions_a = {a.lower().strip() for a in rep_a.actions}
        actions_b = {a.lower().strip() for a in rep_b.actions}

        objects_a = {o.lower().strip() for o in rep_a.objects}
        objects_b = {o.lower().strip() for o in rep_b.objects}

        score = 0.0
        reasons = []

        if summary_a and summary_b:
            if summary_a == summary_b:
                score = 1.0
                reasons.append("Intent summaries match exactly")
            elif summary_a in summary_b or summary_b in summary_a:
                score = 0.8
                reasons.append("Intent summaries overlap partially")
            else:
                score = 0.2
                reasons.append("Intent summaries differ")
        elif not summary_a and not summary_b:
            score = 0.5
            reasons.append("No intent summaries available")
        else:
            score = 0.3
            reasons.append("Only one representation has intent summary")

        if actions_a and actions_b:
            shared_actions = actions_a & actions_b
            if shared_actions:
                score = min(1.0, score + 0.15)
                reasons.append(f"Shared actions: {', '.join(sorted(shared_actions))}")
            elif actions_a and actions_b:
                score = max(0.0, score - 0.1)
                reasons.append("No shared actions")

        if objects_a and objects_b:
            shared_objects = objects_a & objects_b
            if shared_objects:
                score = min(1.0, score + 0.1)
                reasons.append(f"Shared objects: {', '.join(sorted(shared_objects))}")

        score = max(0.0, min(1.0, score))
        confidence = min(1.0, 0.5 + 0.3 * score + 0.2 * (1.0 if summary_a and summary_b else 0.0))

        return {
            "score": score,
            "confidence": confidence,
            "reason": "; ".join(reasons) if reasons else "No intent information available",
            "detail": {
                "summary_a": summary_a,
                "summary_b": summary_b,
                "actions_a": sorted(actions_a),
                "actions_b": sorted(actions_b),
                "objects_a": sorted(objects_a),
                "objects_b": sorted(objects_b),
            },
        }


IntentMatcher = DefaultIntentMatcher
