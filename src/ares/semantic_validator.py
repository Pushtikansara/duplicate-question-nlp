from __future__ import annotations

import re
from typing import Any

ABBREVIATIONS: dict[str, list[str]] = {
    "ai": ["artificial intelligence", "artificial intelligent"],
    "ml": ["machine learning"],
    "nlp": ["natural language processing"],
    "usa": ["united states", "united states of america", "america"],
    "uk": ["united kingdom"],
    "eu": ["european union"],
    "un": ["united nations"],
    "who": ["world health organization"],
    "wto": ["world trade organization"],
    "imf": ["international monetary fund"],
    "nasa": ["national aeronautics and space administration"],
    "fbi": ["federal bureau of investigation"],
    "cia": ["central intelligence agency"],
    "nsa": ["national security agency"],
    "html": ["hypertext markup language"],
    "css": ["cascading style sheets"],
    "js": ["javascript"],
    "api": ["application programming interface"],
    "sdk": ["software development kit"],
    "db": ["database"],
    "os": ["operating system"],
    "gui": ["graphical user interface"],
    "cli": ["command line interface"],
    "json": ["javascript object notation"],
    "xml": ["extensible markup language"],
    "sql": ["structured query language"],
    "nosql": ["not only sql"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud platform"],
    "azure": ["microsoft azure"],
    "cpu": ["central processing unit"],
    "gpu": ["graphics processing unit"],
    "ram": ["random access memory"],
    "ssd": ["solid state drive"],
    "hdd": ["hard disk drive"],
    "url": ["uniform resource locator"],
    "uri": ["uniform resource identifier"],
    "http": ["hypertext transfer protocol"],
    "https": ["hypertext transfer protocol secure"],
    "ftp": ["file transfer protocol"],
    "ssh": ["secure shell"],
    "dns": ["domain name system"],
    "ip": ["internet protocol"],
    "tcp": ["transmission control protocol"],
    "udp": ["user datagram protocol"],
    "api": ["application programming interface"],
    "rest": ["representational state transfer"],
    "soap": ["simple object access protocol"],
    "crud": ["create read update delete"],
    "orm": ["object relational mapping"],
    "mvc": ["model view controller"],
    "mvvm": ["model view viewmodel"],
    "oop": ["object oriented programming"],
    "fp": ["functional programming"],
    "iot": ["internet of things"],
    "qa": ["quality assurance"],
    "faq": ["frequently asked questions"],
    "pdf": ["portable document format"],
    "csv": ["comma separated values"],
    "yaml": ["yaml ain t markup language"],
    "toml": ["tom s obvious minimal language"],
    "ui": ["user interface"],
    "ux": ["user experience"],
    "ide": ["integrated development environment"],
    "cicd": ["continuous integration continuous deployment"],
    "cdn": ["content delivery network"],
    "ddos": ["distributed denial of service"],
    "mitm": ["man in the middle"],
    "xss": ["cross site scripting"],
    "csrf": ["cross site request forgery"],
    "sql_injection": ["sql injection"],
    "rce": ["remote code execution"],
    "pr": ["pull request", "public relations"],
    "wip": ["work in progress"],
    "tldr": ["too long did not read"],
    "btw": ["by the way"],
    "idk": ["i do not know"],
    "imo": ["in my opinion"],
    "imho": ["in my humble opinion"],
    "aka": ["also known as"],
    "e_g": ["for example"],
    "i_e": ["that is"],
    "et_al": ["and others"],
    "etc": ["et cetera"],
    "vs": ["versus"],
    "v": ["versus"],
}

SYNONYMS: dict[str, list[str]] = {
    "buy": ["purchase", "acquire", "get"],
    "sell": ["purchase", "trade", "market"],
    "expensive": ["costly", "pricey", "dear", "high priced"],
    "cheap": ["inexpensive", "affordable", "low cost", "budget"],
    "good": ["excellent", "great", "fine", "superior", "quality"],
    "bad": ["poor", "terrible", "awful", "inferior", "substandard"],
    "big": ["large", "huge", "enormous", "massive", "great", "giant"],
    "small": ["little", "tiny", "compact", "miniature", "petite"],
    "fast": ["quick", "rapid", "swift", "speedy", "brisk"],
    "slow": ["sluggish", "leisurely", "unhurried"],
    "easy": ["simple", "straightforward", "effortless", "uncomplicated"],
    "hard": ["difficult", "challenging", "tough", "arduous"],
    "begin": ["start", "commence", "initiate", "launch"],
    "end": ["finish", "complete", "conclude", "terminate", "stop"],
    "help": ["assist", "aid", "support", "guide"],
    "make": ["create", "build", "produce", "construct", "fabricate"],
    "use": ["utilize", "employ", "apply", "operate"],
    "show": ["display", "demonstrate", "exhibit", "present", "reveal"],
    "find": ["discover", "locate", "uncover", "detect"],
    "need": ["require", "necessitate", "demand"],
    "want": ["desire", "wish", "prefer"],
    "think": ["believe", "consider", "deem", "reckon"],
    "know": ["understand", "comprehend", "grasp"],
    "change": ["modify", "alter", "adjust", "transform"],
    "fix": ["repair", "correct", "resolve", "remedy"],
    "problem": ["issue", "challenge", "difficulty", "trouble"],
    "solution": ["answer", "fix", "resolution", "remedy"],
    "important": ["crucial", "critical", "essential", "vital", "significant"],
    "different": ["distinct", "unique", "dissimilar", "contrasting"],
    "similar": ["alike", "comparable", "analogous", "akin"],
    "true": ["correct", "accurate", "right", "valid", "factual"],
    "false": ["incorrect", "wrong", "invalid", "untrue", "erroneous"],
    "famous": ["well known", "renowned", "celebrated", "prominent"],
    "popular": ["well liked", "trendy", "fashionable", "in demand"],
    "new": ["novel", "fresh", "recent", "modern", "latest"],
    "old": ["ancient", "aged", "elderly", "antique", "vintage"],
    "beautiful": ["attractive", "pretty", "lovely", "gorgeous", "stunning"],
    "ugly": ["unattractive", "hideous", "unsightly", "grotesque"],
    "happy": ["glad", "joyful", "cheerful", "delighted", "content"],
    "sad": ["unhappy", "sorrowful", "miserable", "gloomy", "depressed"],
    "angry": ["furious", "irate", "enraged", "livid", "incensed"],
    "scared": ["afraid", "frightened", "terrified", "fearful", "alarmed"],
    "strange": ["odd", "weird", "peculiar", "unusual", "bizarre"],
    "nice": ["pleasant", "agreeable", "delightful", "enjoyable"],
    "funny": ["humorous", "amusing", "comical", "hilarious", "witty"],
    "smart": ["intelligent", "clever", "bright", "sharp", "brilliant"],
    "stupid": ["dumb", "foolish", "idiotic", "unintelligent"],
    "rich": ["wealthy", "affluent", "prosperous", "well off"],
    "poor": ["destitute", "impoverished", "needy", "indigent"],
    "strong": ["powerful", "robust", "sturdy", "resilient", "mighty"],
    "weak": ["feeble", "frail", "fragile", "delicate", "powerless"],
}

COMMON_TYPOS: dict[str, str] = {
    "recieve": "receive",
    "wierd": "weird",
    "beleive": "believe",
    "acheive": "achieve",
    "adress": "address",
    "alot": "a lot",
    "alot": "a lot",
    "begining": "beginning",
    "beleif": "belief",
    "calender": "calendar",
    "camouflage": "camouflage",
    "catagory": "category",
    "changable": "changeable",
    "cheif": "chief",
    "collectable": "collectible",
    "commitee": "committee",
    "concious": "conscious",
    "curiousity": "curiosity",
    "definately": "definitely",
    "definately": "definitely",
    "disapear": "disappear",
    "disapoint": "disappoint",
    "ecstasy": "ecstasy",
    "embarass": "embarrass",
    "enviroment": "environment",
    "exagerate": "exaggerate",
    "excell": "excel",
    "existance": "existence",
    "extremly": "extremely",
    "febuary": "february",
    "focussed": "focused",
    "foriegn": "foreign",
    "fourty": "forty",
    "foward": "forward",
    "freind": "friend",
    "goverment": "government",
    "grammer": "grammar",
    "gurantee": "guarantee",
    "harrass": "harass",
    "hieght": "height",
    "humourous": "humorous",
    "idiosyncracy": "idiosyncrasy",
    "imaginery": "imaginary",
    "immediatly": "immediately",
    "independant": "independent",
    "interupt": "interrupt",
    "intrest": "interest",
    "irrevelant": "irrelevant",
    "jewlery": "jewelry",
    "judgment": "judgement",
    "knowlege": "knowledge",
    "liason": "liaison",
    "libary": "library",
    "lisence": "license",
    "maintainance": "maintenance",
    "millenium": "millennium",
    "mischievious": "mischievous",
    "mispelling": "misspelling",
    "morgage": "mortgage",
    "neccessary": "necessary",
    "nineth": "ninth",
    "noticable": "noticeable",
    "occassion": "occasion",
    "occurence": "occurrence",
    "opan": "open",
    "oppertunity": "opportunity",
    "optional": "optional",
    "originaly": "originally",
    "paralel": "parallel",
    "parliment": "parliament",
    "percieve": "perceive",
    "persistant": "persistent",
    "personel": "personnel",
    "posession": "possession",
    "potatoe": "potato",
    "practically": "practically",
    "prefered": "preferred",
    "prevelant": "prevalent",
    "privelege": "privilege",
    "probly": "probably",
    "proffessor": "professor",
    "promise": "promise",
    "pronounciation": "pronunciation",
    "psychology": "psychology",
    "publically": "publicly",
    "quizes": "quizzes",
    "reccomend": "recommend",
    "reciept": "receipt",
    "refrence": "reference",
    "remeber": "remember",
    "repetition": "repetition",
    "restaraunt": "restaurant",
    "rhythm": "rhythm",
    "rythm": "rhythm",
    "sargeant": "sergeant",
    "seperate": "separate",
    "seige": "siege",
    "similer": "similar",
    "skilful": "skillful",
    "speach": "speech",
    "sponser": "sponsor",
    "steriod": "steroid",
    "stragedy": "strategy",
    "strenth": "strength",
    "supercede": "supersede",
    "suprise": "surprise",
    "thier": "their",
    "tommorow": "tomorrow",
    "tounge": "tongue",
    "truely": "truly",
    "unforetunately": "unfortunately",
    "untill": "until",
    "vacume": "vacuum",
    "vegetable": "vegetable",
    "vigourous": "vigorous",
    "warrent": "warrant",
    "weild": "wield",
    "wierd": "weird",
    "writen": "written",
    "writting": "writing",
    "yatch": "yacht",
}


def _get_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def expand_abbreviations(text: str) -> str:
    words = text.lower().split()
    expanded = []
    for w in words:
        clean = w.strip(".,!?;:'\"()[]{}")
        if clean in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[clean][0])
        else:
            expanded.append(w)
    return " ".join(expanded)


def fix_typos(text: str) -> str:
    words = text.split()
    fixed = []
    for w in words:
        clean = w.strip(".,!?;:'\"()[]{}")
        lower = clean.lower()
        if lower in COMMON_TYPOS:
            replacement = COMMON_TYPOS[lower]
            if clean[0].isupper():
                replacement = replacement.capitalize()
            fixed.append(replacement)
        else:
            fixed.append(w)
    return " ".join(fixed)


def detect_negation(text: str) -> list[str]:
    negation_words = {
        "not",
        "no",
        "never",
        "neither",
        "nor",
        "none",
        "nothing",
        "nobody",
        "nowhere",
        "cannot",
        "can't",
        "don't",
        "doesn't",
        "didn't",
        "won't",
        "wouldn't",
        "shouldn't",
        "couldn't",
        "isn't",
        "aren't",
        "wasn't",
        "weren't",
        "haven't",
        "hasn't",
        "hadn't",
        "without",
        "lack",
        "lacking",
        "absent",
        "excluding",
    }
    words = set(text.lower().split())
    return [w for w in negation_words if w in words]


def detect_contradiction(q1_words: set[str], q2_words: set[str]) -> list[str]:
    contradictions: list[str] = []
    antonym_pairs = [
        ("not", "is"),
        ("not", "are"),
        ("not", "was"),
        ("not", "were"),
        ("not", "have"),
        ("not", "has"),
        ("not", "had"),
        ("no", "yes"),
        ("true", "false"),
        ("correct", "incorrect"),
        ("right", "wrong"),
        ("positive", "negative"),
        ("good", "bad"),
        ("big", "small"),
        ("large", "small"),
        ("high", "low"),
        ("tall", "short"),
        ("fast", "slow"),
        ("quick", "slow"),
        ("hot", "cold"),
        ("warm", "cool"),
        ("old", "new"),
        ("young", "old"),
        ("cheap", "expensive"),
        ("cheap", "costly"),
        ("easy", "hard"),
        ("easy", "difficult"),
        ("simple", "complex"),
        ("begin", "end"),
        ("start", "finish"),
        ("start", "stop"),
        ("open", "close"),
        ("on", "off"),
        ("in", "out"),
        ("up", "down"),
        ("above", "below"),
        ("over", "under"),
        ("more", "less"),
        ("many", "few"),
        ("increase", "decrease"),
        ("rise", "fall"),
        ("grow", "shrink"),
        ("gain", "lose"),
        ("win", "lose"),
        ("success", "failure"),
        ("pass", "fail"),
        ("love", "hate"),
        ("like", "dislike"),
        ("agree", "disagree"),
        ("accept", "reject"),
        ("approve", "deny"),
        ("allow", "forbid"),
        ("include", "exclude"),
        ("add", "remove"),
        ("enter", "exit"),
        ("arrive", "leave"),
        ("come", "go"),
        ("buy", "sell"),
        ("give", "take"),
        ("lend", "borrow"),
        ("teach", "learn"),
        ("ask", "answer"),
        ("question", "answer"),
    ]
    for a, b in antonym_pairs:
        if a in q1_words and b in q2_words:
            contradictions.append(f"'{a}' vs '{b}'")
        if b in q1_words and a in q2_words:
            contradictions.append(f"'{b}' vs '{a}'")
    return contradictions


def detect_negation_contradiction(q1_negations: list[str], q2_negations: list[str]) -> list[str]:
    conflicts: list[str] = []
    for n in q1_negations:
        if n not in q2_negations:
            conflicts.append(f"negation mismatch: '{n}' only in Q1")
    for n in q2_negations:
        if n not in q1_negations:
            conflicts.append(f"negation mismatch: '{n}' only in Q2")
    q1_has_neg = len(q1_negations) > 0
    q2_has_neg = len(q2_negations) > 0
    if q1_has_neg != q2_has_neg:
        if q1_has_neg:
            conflicts.append("Q1 negated, Q2 not negated → likely contradiction")
        else:
            conflicts.append("Q2 negated, Q1 not negated → likely contradiction")
    return conflicts


def check_semantic_similarity(q1: str, q2: str, prediction_confidence: float) -> dict[str, Any]:
    q1_words = _get_words(q1)
    q2_words = _get_words(q2)
    overlap = q1_words & q2_words
    jaccard = len(overlap) / len(q1_words | q2_words) if (q1_words | q2_words) else 0.0

    synonym_matches = 0
    for word in q1_words:
        if word in SYNONYMS:
            for syn in SYNONYMS[word]:
                if syn in q2_words or any(s in q2_words for s in syn.split()):
                    synonym_matches += 1
                    break

    for word2 in q2_words:
        if word2 in SYNONYMS:
            for syn in SYNONYMS[word2]:
                if syn in q1_words or any(s in q1_words for s in syn.split()):
                    synonym_matches += 1
                    break

    q1_negations = detect_negation(q1)
    q2_negations = detect_negation(q2)
    negation_conflicts = detect_negation_contradiction(q1_negations, q2_negations)
    antonym_conflicts = detect_contradiction(q1_words, q2_words)
    all_conflicts = negation_conflicts + antonym_conflicts

    abbreviation_overlap = 0
    for abbr, expansions in ABBREVIATIONS.items():
        if abbr in q1_words or any(exp in q1.lower() for exp in expansions):
            if abbr in q2_words or any(exp in q2.lower() for exp in expansions):
                abbreviation_overlap += 1

    return {
        "jaccard_similarity": round(jaccard, 4),
        "word_overlap": sorted(overlap),
        "overlap_count": len(overlap),
        "synonym_matches": synonym_matches,
        "abbreviation_overlap": abbreviation_overlap,
        "negation_q1": q1_negations,
        "negation_q2": q2_negations,
        "negation_conflicts": negation_conflicts,
        "antonym_conflicts": antonym_conflicts,
        "contradiction_count": len(all_conflicts),
        "has_contradiction": len(all_conflicts) > 0,
    }


def compute_semantic_penalty(q1: str, q2: str, prediction_confidence: float) -> tuple[float, dict[str, Any]]:
    semantic = check_semantic_similarity(q1, q2, prediction_confidence)
    penalty = 0.0
    reasons: list[str] = []

    if semantic["contradiction_count"] > 0:
        penalty += min(0.4, semantic["contradiction_count"] * 0.15)
        reasons.append(f"contradiction detected ({semantic['contradiction_count']} conflicts)")

    if semantic["negation_conflicts"]:
        penalty += 0.2
        reasons.append("negation mismatch between questions")

    if semantic["jaccard_similarity"] < 0.1 and prediction_confidence > 0.8:
        penalty += 0.15
        reasons.append("low lexical overlap despite high confidence")

    if semantic["synonym_matches"] > 0 and prediction_confidence < 0.3:
        penalty -= min(0.2, semantic["synonym_matches"] * 0.1)
        reasons.append("synonym overlap suggests potential duplicate")

    if semantic["abbreviation_overlap"] > 0:
        penalty -= min(0.15, semantic["abbreviation_overlap"] * 0.05)
        reasons.append("abbreviation overlap detected")

    penalty = max(-0.3, min(0.5, penalty))

    return penalty, semantic


def validate_semantic(q1: str, q2: str, prediction_result: Any) -> dict[str, Any]:
    penalty, semantic_detail = compute_semantic_penalty(q1, q2, prediction_result.confidence)
    original_confidence = float(prediction_result.confidence)
    adjusted_confidence = max(0.05, min(0.99, original_confidence - penalty))
    ambiguity = penalty > 0.05 or semantic_detail["contradiction_count"] > 0

    return {
        "adjusted_confidence": adjusted_confidence,
        "semantic_penalty": round(penalty, 4),
        "ambiguity_detected": ambiguity,
        "adjustment_applied": abs(penalty) > 0.01,
        "original_confidence": original_confidence,
        "semantic_detail": semantic_detail,
        "reasoning": _build_semantic_reasoning(penalty, semantic_detail),
    }


def _build_semantic_reasoning(penalty: float, detail: dict[str, Any]) -> str:
    parts: list[str] = []
    if detail["contradiction_count"] > 0:
        for c in detail.get("antonym_conflicts", []):
            parts.append(f"antonym: {c}")
        for c in detail.get("negation_conflicts", []):
            parts.append(f"negation: {c}")
    if detail["synonym_matches"] > 0:
        parts.append(f"{detail['synonym_matches']} synonym match(es)")
    if detail["abbreviation_overlap"] > 0:
        parts.append(f"{detail['abbreviation_overlap']} abbreviation overlap(s)")
    if detail["jaccard_similarity"] < 0.2:
        parts.append(f"low lexical overlap ({detail['jaccard_similarity']:.1%})")
    if abs(penalty) > 0.01:
        direction = "reduced" if penalty > 0 else "increased"
        parts.append(f"confidence {direction} by {abs(penalty):.1%}")
    return "; ".join(parts) if parts else "No semantic issues detected"
