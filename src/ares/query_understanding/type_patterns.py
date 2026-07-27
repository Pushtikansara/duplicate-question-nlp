from __future__ import annotations

import re

QUESTION_TYPES = frozenset(
    {
        "definition",
        "how_to",
        "comparison",
        "explanation",
        "reason_why",
        "opinion",
        "factoid",
        "yes_no",
        "numeric",
        "temporal",
        "location",
        "person",
        "organization",
        "procedure",
        "recommendation",
        "troubleshooting",
        "code",
        "list",
        "other",
    }
)

PAIR_TYPES = frozenset(
    {
        "same_type",
        "different_type",
        "complementary",
        "potential_paraphrase",
        "potential_reformulation",
        "unknown",
    }
)

FIRST_WORD_RULES: dict[str, set[str]] = {
    "definition": {"what", "define", "describe"},
    "how_to": {"how"},
    "reason_why": {"why"},
    "yes_no": {
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "did",
        "has",
        "have",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "am",
        "be",
        "been",
        "being",
        "doing",
    },
    "temporal": {"when"},
    "location": {"where"},
    "person": {"who"},
    "organization": {"which"},
}

DEFINITION_PATTERNS = [
    re.compile(r"\bwhat\s+is\s+a(?:n)?\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:definition|meaning|concept)\s+of\b", re.IGNORECASE),
    re.compile(r"\bdefine\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:does|is)\s+.+\s+mean\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+are\b", re.IGNORECASE),
    re.compile(r"\bdescribe\b", re.IGNORECASE),
]

HOW_TO_PATTERNS = [
    re.compile(r"\bhow\s+to\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:do|does|did|can|would)\s+(?:i|you|we|they|one)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:is|are|was|were)\s+.+\s+(?:done|made|created|built|written|implemented)\b", re.IGNORECASE),
    re.compile(r"\bway\s+to\b", re.IGNORECASE),
    re.compile(r"\btutorial\s+(?:on|for|about)\b", re.IGNORECASE),
    re.compile(r"\bguide\s+(?:on|for|to)\b", re.IGNORECASE),
]

COMPARISON_PATTERNS = [
    re.compile(r"\b(differen|compar|vs\.?|versus)\b", re.IGNORECASE),
    re.compile(r"\bcompare\b", re.IGNORECASE),
    re.compile(r"\bcontrast\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+is\s+(?:better|worse|faster|stronger|bigger|smaller)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:difference|similarity)\s+between\b", re.IGNORECASE),
    re.compile(r"\bpros?\s+and\s+cons\b", re.IGNORECASE),
    re.compile(r"\badvantage|disadvantage\b", re.IGNORECASE),
    re.compile(r"\bvs\b", re.IGNORECASE),
]

EXPLANATION_PATTERNS = [
    re.compile(r"\bexplain\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:does|is)\s+.+\s+(?:do|mean|work)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:does|do|did)\s+.+\s+work\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:reason|purpose|cause)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+happens?\s+(?:when|if)\b", re.IGNORECASE),
    re.compile(r"\bcan\s+you\s+explain\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+does\s+that\s+mean\b", re.IGNORECASE),
]

REASON_WHY_PATTERNS = [
    re.compile(r"\bwhy\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:causes?|is\s+the\s+(?:reason|cause|purpose))\b", re.IGNORECASE),
    re.compile(r"\bhow\s+come\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:point|motivation)\b", re.IGNORECASE),
    re.compile(r"\bfor\s+what\s+reason\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+would\s+happen\s+if\b", re.IGNORECASE),
]

OPINION_PATTERNS = [
    re.compile(r"\b(?:do|would|could)\s+you\s+(?:think|believe|consider|recommend)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:is\s+)?your\s+(?:opinion|thought|take|view|feeling)s?\b", re.IGNORECASE),
    re.compile(r"\bin\s+your\s+opinion\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+do\s+you\s+(?:think|feel|believe|reckon)\b", re.IGNORECASE),
    re.compile(r"\bis\s+it\s+(?:good|bad|worth|better)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+best\b", re.IGNORECASE),
    re.compile(r"\bshould\s+(?:i|you|we|they)\b", re.IGNORECASE),
    re.compile(r"\bwould\s+you\s+(?:recommend|suggest)\b", re.IGNORECASE),
]

FACTOID_PATTERNS = [
    re.compile(r"\bwho\s+(?:is|are|was|were|invented|created|discovered|founded|wrote|made)\b", re.IGNORECASE),
    re.compile(r"\bwhen\s+(?:was|were|did|is|are)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:year|century|era)\b", re.IGNORECASE),
    re.compile(r"\bwho\s+invented\b", re.IGNORECASE),
    re.compile(r"\bwho\s+discovered\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:population|height|length|size|distance|speed|weight)\b", re.IGNORECASE),
]

YES_NO_PATTERNS = [
    re.compile(
        r"^(?:is|are|was|were|do|does|did|has|have|can|could|will|would|shall|should|may|might)\b", re.IGNORECASE
    ),
]

NUMERIC_PATTERNS = [
    re.compile(r"\bhow\s+(?:many|much|long|far|tall|wide|deep|old|often|frequently|expensive)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:price|cost|number|count|total|amount)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:is|are)\s+the\s+(?:statistics?|figures?|rates?|percentages?)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+percentage?\b", re.IGNORECASE),
]

TEMPORAL_PATTERNS = [
    re.compile(r"^when\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:time|date|day|month|year|century|era)\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(?:long|old|often|frequently)\b", re.IGNORECASE),
]

LOCATION_PATTERNS = [
    re.compile(r"\bwhere\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:place|location|city|country|region|area|state|capital)\b", re.IGNORECASE),
    re.compile(r"\bin\s+which\s+(?:place|location|city|country|region)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+is\s+the\s+(?:address|coordinates|location)\b", re.IGNORECASE),
]

PERSON_PATTERNS = [
    re.compile(r"\bwho\b", re.IGNORECASE),
    re.compile(r"\bwhom\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:person|people|individual|name|author|creator|founder|ceo)\b", re.IGNORECASE),
    re.compile(r"\bwhose\b", re.IGNORECASE),
]

ORGANIZATION_PATTERNS = [
    re.compile(
        r"\bwhat\s+(?:company|organization|institution|university|college|school|department|agency|firm|corporation|team|group|club|society)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwhich\s+(?:company|organization)\b", re.IGNORECASE),
]

PROCEDURE_PATTERNS = [
    re.compile(r"\bhow\s+to\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:are|is)\s+the\s+(?:steps|procedure|process|method|approach|technique)\b", re.IGNORECASE),
    re.compile(r"\bsteps?\s+(?:to|for|involved|required|needed)\b", re.IGNORECASE),
    re.compile(r"\bprocess\s+(?:of|for)\b", re.IGNORECASE),
    re.compile(r"\bprocedure\s+(?:for|to)\b", re.IGNORECASE),
    re.compile(
        r"\bhow\s+(?:can|do)\s+(?:i|you|we)\s+(?:set\s+up|install|configure|deploy|create|build|write|implement)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\balgorithm\s+(?:for|to)\b", re.IGNORECASE),
    re.compile(r"\brecipe\s+(?:for|to)\b", re.IGNORECASE),
]

RECOMMENDATION_PATTERNS = [
    re.compile(r"\bwhat\s+is\s+the\s+best\b", re.IGNORECASE),
    re.compile(r"\bwhich\s+.+\s+(?:is\s+)?(?:better|best|recommended|should)\b", re.IGNORECASE),
    re.compile(r"\brecommend\b", re.IGNORECASE),
    re.compile(r"\bsuggest\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+.+\s+(?:should|ought)\s+(?:i|you|we)\b", re.IGNORECASE),
    re.compile(r"\btop\s+(?:\d+\s+)?(?:tips?|recommendations?|picks?|tools?|books?|resources?)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:are|is)\s+the\s+(?:best|top)\b", re.IGNORECASE),
]

TROUBLESHOOTING_PATTERNS = [
    re.compile(
        r"\b(?:fix|solve|resolve|debug|troubleshoot|repair|error|bug|issue|problem|crash|fail|broken|not\s+working)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bhow\s+to\s+(?:fix|solve|resolve|debug|repair)\b", re.IGNORECASE),
    re.compile(r"\bwhy\s+(?:is|are|does|do)\s+.+\s+(?:broken|failing|not\s+working|crashing)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(?:is\s+)?wrong\b", re.IGNORECASE),
    re.compile(r"\berror\b", re.IGNORECASE),
    re.compile(r"\bexception\b", re.IGNORECASE),
    re.compile(r"\bnot\s+working\b", re.IGNORECASE),
    re.compile(r"\bunexpected\b", re.IGNORECASE),
]

LIST_PATTERNS = [
    re.compile(r"\blist\b", re.IGNORECASE),
    re.compile(
        r"\bwhat\s+are\s+(?:the\s+)?(?:types?|kinds?|sorts?|categories?|varieties?|examples?|instances?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bname\s+(?:the|some|a\s+few|all)\b", re.IGNORECASE),
    re.compile(r"\benumerate\b", re.IGNORECASE),
    re.compile(r"\bgive\s+me\s+(?:the|some|a\s+list)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+are\s+some\b", re.IGNORECASE),
]

TYPE_PATTERNS: dict[str, list[re.Pattern]] = {
    "definition": DEFINITION_PATTERNS,
    "how_to": HOW_TO_PATTERNS,
    "comparison": COMPARISON_PATTERNS,
    "explanation": EXPLANATION_PATTERNS,
    "reason_why": REASON_WHY_PATTERNS,
    "opinion": OPINION_PATTERNS,
    "factoid": FACTOID_PATTERNS,
    "yes_no": YES_NO_PATTERNS,
    "numeric": NUMERIC_PATTERNS,
    "temporal": TEMPORAL_PATTERNS,
    "location": LOCATION_PATTERNS,
    "person": PERSON_PATTERNS,
    "organization": ORGANIZATION_PATTERNS,
    "procedure": PROCEDURE_PATTERNS,
    "recommendation": RECOMMENDATION_PATTERNS,
    "troubleshooting": TROUBLESHOOTING_PATTERNS,
    "list": LIST_PATTERNS,
}

COMPLEMENTARY_PAIRS: dict[str, set[str]] = {
    "definition": {"how_to", "explanation", "procedure"},
    "how_to": {"definition", "troubleshooting", "procedure", "explanation"},
    "explanation": {"definition", "how_to", "reason_why"},
    "reason_why": {"explanation", "troubleshooting"},
    "comparison": {"recommendation"},
    "recommendation": {"comparison"},
    "troubleshooting": {"how_to", "reason_why", "explanation"},
    "code": {"how_to", "troubleshooting", "definition", "explanation"},
    "factoid": {"definition", "temporal", "location", "person"},
    "procedure": {"how_to", "definition", "explanation"},
}

MUTUALLY_EXCLUSIVE: dict[str, set[str]] = {
    "yes_no": {"definition", "numeric", "temporal", "location", "list"},
    "opinion": {"definition", "factoid", "numeric"},
    "list": {"yes_no", "opinion"},
}

COMPLEMENTARY_PATTERN_SCORES: dict[tuple[str, str], float] = {
    ("definition", "how_to"): 0.75,
    ("how_to", "definition"): 0.75,
    ("definition", "explanation"): 0.80,
    ("explanation", "definition"): 0.80,
    ("how_to", "procedure"): 0.85,
    ("procedure", "how_to"): 0.85,
    ("reason_why", "explanation"): 0.70,
    ("troubleshooting", "how_to"): 0.75,
    ("comparison", "recommendation"): 0.60,
    ("code", "how_to"): 0.65,
    ("code", "troubleshooting"): 0.65,
    ("factoid", "temporal"): 0.60,
}
