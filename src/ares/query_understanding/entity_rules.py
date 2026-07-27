from __future__ import annotations

import re

from ares.query_understanding.entity_models import Entity

_CURRENCY_SYMBOLS = re.compile(r"[$€£¥₹₽₩₪₫₱₾₿]")
_PERCENTAGE_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\s*%")
_VERSION_PATTERN = re.compile(r"\b\d+\.\d+(?:\.\d+)*(?:[a-zA-Z]*(?:-\d+)?)?\b")
_NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
_TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?\b")
_URL_PATTERN = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?"
    r"(?:/[\w\-./?%&+=~!#]*)?",
    re.IGNORECASE,
)
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_FILE_PATTERN = re.compile(
    r"\b[\w.\-]+\.(?:py|js|ts|java|cpp|c|h|hpp|cs|go|rs|rb|php|swift|kt|"
    r"scala|ex|exs|sh|bash|zsh|yml|yaml|json|xml|toml|ini|cfg|conf|"
    r"md|rst|txt|csv|tsv|sql|r|m|mm|pl|pm|lua|hs|ml|clj|cljs|cljc|"
    r"dart|fs|fsx|vb|bat|ps1|dockerfile|makefile|gradle|sbt|cabal)\b",
    re.IGNORECASE,
)

_PROGRAMMING_LANGUAGES: dict[str, float] = {
    "python": 1.0,
    "javascript": 1.0,
    "typescript": 1.0,
    "java": 1.0,
    "c++": 1.0,
    "csharp": 1.0,
    "c#": 1.0,
    "ruby": 1.0,
    "php": 1.0,
    "swift": 1.0,
    "kotlin": 1.0,
    "go": 1.0,
    "golang": 1.0,
    "rust": 1.0,
    "scala": 1.0,
    "perl": 1.0,
    "lua": 1.0,
    "haskell": 1.0,
    "clojure": 1.0,
    "elixir": 1.0,
    "erlang": 1.0,
    "dart": 1.0,
    "f#": 1.0,
    "fsharp": 1.0,
    "r": 1.0,
    "matlab": 1.0,
    "julia": 1.0,
    "sql": 1.0,
    "bash": 1.0,
    "shell": 1.0,
    "pascal": 1.0,
    "fortran": 1.0,
    "cobol": 1.0,
    "assembly": 1.0,
    "html": 1.0,
    "css": 1.0,
    "sass": 1.0,
    "less": 1.0,
    "graphql": 1.0,
    "regex": 1.0,
    "yaml": 1.0,
    "json": 1.0,
    "xml": 1.0,
    "markdown": 1.0,
    "latex": 1.0,
    "verilog": 1.0,
    "vhdl": 1.0,
}

_FRAMEWORKS: dict[str, float] = {
    "django": 1.0,
    "flask": 1.0,
    "fastapi": 1.0,
    "spring": 1.0,
    "spring boot": 1.0,
    "rails": 1.0,
    "ruby on rails": 1.0,
    "laravel": 1.0,
    "symfony": 1.0,
    "express": 1.0,
    "next.js": 1.0,
    "nextjs": 1.0,
    "nuxt": 1.0,
    "react": 1.0,
    "react.js": 1.0,
    "vue": 1.0,
    "vue.js": 1.0,
    "angular": 1.0,
    "svelte": 1.0,
    "jquery": 1.0,
    "bootstrap": 1.0,
    "tailwind": 1.0,
    "tailwind css": 1.0,
    "tensorflow": 1.0,
    "pytorch": 1.0,
    "keras": 1.0,
    "scikit-learn": 1.0,
    "sklearn": 1.0,
    "pandas": 1.0,
    "numpy": 1.0,
    "scipy": 1.0,
    "matplotlib": 1.0,
    "seaborn": 1.0,
    "opencv": 1.0,
    "nltk": 1.0,
    "spacy": 1.0,
    "transformers": 1.0,
    "huggingface": 1.0,
    "hugging face": 1.0,
    "jupyter": 1.0,
    "node.js": 1.0,
    "nodejs": 1.0,
    "deno": 1.0,
    "bun": 1.0,
    "asp.net": 1.0,
    "dotnet": 1.0,
    ".net": 1.0,
    "ktor": 1.0,
    "gin": 1.0,
    "echo": 1.0,
    "fiber": 1.0,
    "akka": 1.0,
    "play": 1.0,
    "catalyst": 1.0,
    "zend": 1.0,
    "codeigniter": 1.0,
    "cakephp": 1.0,
    "yii": 1.0,
}

_LIBRARIES: dict[str, float] = {
    "requests": 1.0,
    "beautifulsoup": 1.0,
    "selenium": 1.0,
    "puppeteer": 1.0,
    "cheerio": 1.0,
    "lodash": 1.0,
    "moment": 1.0,
    "axios": 1.0,
    "redux": 1.0,
    "vuex": 1.0,
    "pinia": 1.0,
    "mocha": 1.0,
    "chai": 1.0,
    "jest": 1.0,
    "pytest": 1.0,
    "unittest": 1.0,
    "cypress": 1.0,
    "playwright": 1.0,
    "webpack": 1.0,
    "vite": 1.0,
    "esbuild": 1.0,
    "babel": 1.0,
    "gulp": 1.0,
    "grunt": 1.0,
    "npm": 1.0,
    "yarn": 1.0,
    "pnpm": 1.0,
    "pip": 1.0,
    "conda": 1.0,
    "poetry": 1.0,
    "docker": 1.0,
    "kubernetes": 1.0,
    "k8s": 1.0,
    "terraform": 1.0,
    "ansible": 1.0,
    "chef": 1.0,
    "puppet": 1.0,
    "jenkins": 1.0,
    "github actions": 1.0,
    "gitlab ci": 1.0,
    "circleci": 1.0,
    "travis ci": 1.0,
}

_OPERATING_SYSTEMS: dict[str, float] = {
    "linux": 1.0,
    "ubuntu": 1.0,
    "debian": 1.0,
    "centos": 1.0,
    "red hat": 1.0,
    "fedora": 1.0,
    "arch": 1.0,
    "manjaro": 1.0,
    "windows": 1.0,
    "macos": 1.0,
    "mac os": 1.0,
    "os x": 1.0,
    "android": 1.0,
    "ios": 1.0,
    "ipados": 1.0,
    "tvos": 1.0,
    "watchos": 1.0,
    "freebsd": 1.0,
    "openbsd": 1.0,
    "netbsd": 1.0,
    "solaris": 1.0,
    "aix": 1.0,
    "hp-ux": 1.0,
    "chromeos": 1.0,
    "kali": 1.0,
    "raspbian": 1.0,
    "alpine": 1.0,
    "gentoo": 1.0,
    "slackware": 1.0,
    "opensuse": 1.0,
    "mint": 1.0,
    "pop!_os": 1.0,
}

_COMPANIES: dict[str, float] = {
    "google": 1.0,
    "alphabet": 1.0,
    "microsoft": 1.0,
    "apple": 1.0,
    "amazon": 1.0,
    "aws": 1.0,
    "meta": 1.0,
    "facebook": 1.0,
    "netflix": 1.0,
    "tesla": 1.0,
    "spacex": 1.0,
    "openai": 1.0,
    "ibm": 1.0,
    "intel": 1.0,
    "amd": 1.0,
    "nvidia": 1.0,
    "oracle": 1.0,
    "sap": 1.0,
    "salesforce": 1.0,
    "adobe": 1.0,
    "spotify": 1.0,
    "uber": 1.0,
    "airbnb": 1.0,
    "twitter": 1.0,
    "x": 1.0,
    "linkedin": 1.0,
    "slack": 1.0,
    "github": 1.0,
    "gitlab": 1.0,
    "bitbucket": 1.0,
    "docker inc": 1.0,
    "red hat": 1.0,
    "canonical": 1.0,
    "mozilla": 1.0,
    "samsung": 1.0,
    "sony": 1.0,
    "nintendo": 1.0,
    "discord": 1.0,
    "zoom": 1.0,
    "stripe": 1.0,
    "square": 1.0,
    "paypal": 1.0,
    "shopify": 1.0,
    "wordpress": 1.0,
    "automattic": 1.0,
    "mongodb": 1.0,
    "elastic": 1.0,
    "datadog": 1.0,
    "new relic": 1.0,
    "sentry": 1.0,
    "hashicorp": 1.0,
    "cloudflare": 1.0,
    "fastly": 1.0,
}

_PRODUCTS: dict[str, float] = {
    "iphone": 1.0,
    "ipad": 1.0,
    "macbook": 1.0,
    "imac": 1.0,
    "airpods": 1.0,
    "apple watch": 1.0,
    "apple tv": 1.0,
    "galaxy": 1.0,
    "pixel": 1.0,
    "surface": 1.0,
    "kindle": 1.0,
    "echo": 1.0,
    "alexa": 1.0,
    "ring": 1.0,
    "nest": 1.0,
    "chromecast": 1.0,
    "fire tv": 1.0,
    "roku": 1.0,
    "playstation": 1.0,
    "xbox": 1.0,
    "nintendo switch": 1.0,
    "raspberry pi": 1.0,
    "arduino": 1.0,
    "gpt-4": 1.0,
    "gpt-3": 1.0,
    "chatgpt": 1.0,
    "copilot": 1.0,
    "dall-e": 1.0,
    "midjourney": 1.0,
    "stable diffusion": 1.0,
    "vs code": 1.0,
    "visual studio": 1.0,
    "intellij": 1.0,
    "pycharm": 1.0,
    "vim": 1.0,
    "neovim": 1.0,
    "emacs": 1.0,
    "sublime text": 1.0,
    "atom": 1.0,
    "notepad++": 1.0,
}

_COUNTRIES: dict[str, float] = {
    "united states": 1.0,
    "usa": 1.0,
    "us": 0.8,
    "america": 0.8,
    "canada": 1.0,
    "mexico": 1.0,
    "brazil": 1.0,
    "argentina": 1.0,
    "united kingdom": 1.0,
    "uk": 1.0,
    "britain": 1.0,
    "england": 0.9,
    "france": 1.0,
    "germany": 1.0,
    "italy": 1.0,
    "spain": 1.0,
    "china": 1.0,
    "japan": 1.0,
    "india": 1.0,
    "south korea": 1.0,
    "australia": 1.0,
    "russia": 1.0,
    "netherlands": 1.0,
    "sweden": 1.0,
    "norway": 1.0,
    "denmark": 1.0,
    "finland": 1.0,
    "switzerland": 1.0,
    "singapore": 1.0,
    "israel": 1.0,
    "turkey": 1.0,
    "uae": 1.0,
    "saudi arabia": 1.0,
    "egypt": 1.0,
    "nigeria": 1.0,
    "kenya": 1.0,
    "south africa": 1.0,
    "new zealand": 1.0,
    "poland": 1.0,
    "portugal": 1.0,
    "austria": 1.0,
    "belgium": 1.0,
    "greece": 1.0,
    "ireland": 1.0,
    "hungary": 1.0,
    "czech republic": 1.0,
    "romania": 1.0,
    "ukraine": 1.0,
    "vietnam": 1.0,
    "thailand": 1.0,
    "indonesia": 1.0,
    "malaysia": 1.0,
    "philippines": 1.0,
    "pakistan": 1.0,
    "bangladesh": 1.0,
    "chile": 1.0,
    "colombia": 1.0,
    "peru": 1.0,
}

_CITIES: dict[str, float] = {
    "new york": 1.0,
    "london": 1.0,
    "paris": 1.0,
    "tokyo": 1.0,
    "shanghai": 1.0,
    "beijing": 1.0,
    "mumbai": 1.0,
    "delhi": 1.0,
    "seoul": 1.0,
    "sydney": 1.0,
    "berlin": 1.0,
    "moscow": 1.0,
    "dubai": 1.0,
    "singapore": 1.0,
    "hong kong": 1.0,
    "bangkok": 1.0,
    "los angeles": 1.0,
    "chicago": 1.0,
    "san francisco": 1.0,
    "toronto": 1.0,
    "mexico city": 1.0,
    "sao paulo": 1.0,
    "cairo": 1.0,
    "istanbul": 1.0,
    "rome": 1.0,
    "madrid": 1.0,
    "barcelona": 1.0,
    "amsterdam": 1.0,
    "san jose": 0.9,
    "seattle": 1.0,
    "boston": 1.0,
    "austin": 1.0,
    "denver": 1.0,
    "washington dc": 1.0,
    "las vegas": 1.0,
    "miami": 1.0,
    "atlanta": 1.0,
    "portland": 1.0,
}

_LOCATIONS: dict[str, float] = {
    "silicon valley": 1.0,
    "wall street": 1.0,
    "bay area": 1.0,
    "middle east": 1.0,
    "europe": 1.0,
    "asia": 1.0,
    "africa": 1.0,
    "north america": 1.0,
    "south america": 1.0,
    "antarctica": 1.0,
    "pacific ocean": 1.0,
    "atlantic ocean": 1.0,
    "mediterranean": 1.0,
    "sahara": 1.0,
    "amazon": 1.0,
    "himalayas": 1.0,
    "alps": 1.0,
}

_EVENTS: dict[str, float] = {
    "world war 2": 1.0,
    "world war ii": 1.0,
    "ww2": 1.0,
    "world war 1": 1.0,
    "world war i": 1.0,
    "ww1": 1.0,
    "cold war": 1.0,
    "industrial revolution": 1.0,
    "french revolution": 1.0,
    "american revolution": 1.0,
    "super bowl": 1.0,
    "world cup": 1.0,
    "olympics": 1.0,
    "covid": 1.0,
    "covid-19": 1.0,
    "pandemic": 0.8,
    "great depression": 1.0,
    "renaissance": 1.0,
    "hackathon": 0.8,
    "conference": 0.7,
}

_ACADEMIC_SUBJECTS: dict[str, float] = {
    "mathematics": 1.0,
    "math": 1.0,
    "physics": 1.0,
    "chemistry": 1.0,
    "biology": 1.0,
    "computer science": 1.0,
    "cs": 0.8,
    "engineering": 1.0,
    "medicine": 1.0,
    "economics": 1.0,
    "psychology": 1.0,
    "philosophy": 1.0,
    "history": 1.0,
    "geography": 1.0,
    "literature": 1.0,
    "linguistics": 1.0,
    "sociology": 1.0,
    "political science": 1.0,
    "anthropology": 1.0,
    "astronomy": 1.0,
    "geology": 1.0,
    "statistics": 1.0,
    "algebra": 1.0,
    "calculus": 1.0,
    "geometry": 1.0,
    "trigonometry": 1.0,
    "linear algebra": 1.0,
    "probability": 1.0,
    "data science": 1.0,
    "machine learning": 1.0,
    "ml": 0.8,
    "artificial intelligence": 1.0,
    "ai": 0.8,
    "deep learning": 1.0,
    "nlp": 1.0,
    "natural language processing": 1.0,
    "quantum computing": 1.0,
    "cybersecurity": 1.0,
    "blockchain": 1.0,
    "robotics": 1.0,
}

_PERSONS: dict[str, float] = {
    "einstein": 1.0,
    "newton": 1.0,
    "darwin": 1.0,
    "galileo": 1.0,
    "tesla": 0.9,
    "curie": 1.0,
    "turing": 1.0,
    "von neumann": 1.0,
    "bohr": 1.0,
    "feynman": 1.0,
    "hawking": 1.0,
    "pasteur": 1.0,
    "mendel": 1.0,
    "lavoisier": 1.0,
    "copernicus": 1.0,
    "shakespeare": 1.0,
    "plato": 1.0,
    "aristotle": 1.0,
    "socrates": 1.0,
    "nietzsche": 1.0,
    "kant": 1.0,
    "descartes": 1.0,
    "freud": 1.0,
    "jung": 1.0,
    "mozart": 1.0,
    "beethoven": 1.0,
    "picasso": 1.0,
    "vinci": 1.0,
    "michelangelo": 1.0,
    "gates": 0.9,
    "jobs": 0.9,
    "musk": 0.9,
    "bezos": 0.9,
    "zuckerberg": 0.9,
    "page": 0.8,
    "brin": 0.8,
    "torvalds": 1.0,
    "stallman": 1.0,
    "gosling": 1.0,
    "ritchie": 1.0,
    "thompson": 0.8,
    "berners-lee": 1.0,
    "knuth": 1.0,
    "norvig": 1.0,
    "hinton": 1.0,
    "lecun": 1.0,
    "bengio": 1.0,
    "ng": 0.9,
    "karpathy": 1.0,
    "linus": 0.7,
}

_DICTIONARIES: list[tuple[str, dict[str, float], str]] = [
    ("programming_language", _PROGRAMMING_LANGUAGES, "PROGRAMMING_LANGUAGE"),
    ("framework", _FRAMEWORKS, "FRAMEWORK"),
    ("library", _LIBRARIES, "LIBRARY"),
    ("operating_system", _OPERATING_SYSTEMS, "OPERATING_SYSTEM"),
    ("company", _COMPANIES, "COMPANY"),
    ("product", _PRODUCTS, "PRODUCT"),
    ("country", _COUNTRIES, "COUNTRY"),
    ("city", _CITIES, "CITY"),
    ("location", _LOCATIONS, "LOCATION"),
    ("event", _EVENTS, "EVENT"),
    ("academic_subject", _ACADEMIC_SUBJECTS, "ACADEMIC_SUBJECT"),
    ("person", _PERSONS, "PERSON"),
]

_PERSON_TITLE_PATTERN = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sir|Queen|King|President|CEO|CTO|CFO|"
    r"Founder|Director|Manager|Professor|Doctor|Captain|General|Admiral)"
    r"\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)

_CAPITALIZED_NAME = re.compile(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2}\b")

_ORGANIZATION_KEYWORDS = {
    "inc",
    "corp",
    "llc",
    "ltd",
    "co",
    "company",
    "corporation",
    "foundation",
    "institute",
    "university",
    "college",
    "school",
    "association",
    "society",
    "organization",
    "committee",
    "agency",
    "department",
    "ministry",
    "bureau",
    "council",
    "board",
    "studio",
    "studios",
    "lab",
    "labs",
    "group",
    "team",
    "club",
    "bank",
    "fund",
    "funds",
    "hospital",
    "clinic",
    "gmbh",
    "sa",
}

_BOOK_MOVIE_PATTERN = re.compile(
    r"(?:book|movie|film|novel|series|show|game|album|song|play|musical)\s+"
    r"(?:\"([^\"]+)\"|'([^']+)'|`([^`]+)`|([A-Z][a-zA-Z0-9\s]+))"
)

_CURRENCY_PATTERN = re.compile(
    r"[$€£¥₹₽₩₪₫₱₾₿]\s*\d+(?:[.,]\d+)*|\b\d+(?:[.,]\d+)*\s*(?:dollars|euros|pounds|yen|rupees|rubles|won|shekels|dong|pesos)\b",
    re.IGNORECASE,
)


def extract_entities(text: str) -> list[Entity]:
    if not text or not text.strip():
        return []
    entities: list[Entity] = []
    seen_spans: set[tuple[int, int]] = set()

    text_lower = text.lower().strip()

    def _add(entity: Entity) -> None:
        span = (entity.start, entity.end)
        if span not in seen_spans:
            seen_spans.add(span)
            entities.append(entity)

    _extract_dictionary(text, text_lower, _add)
    _extract_regex(text, text_lower, _add)
    _extract_organization(text, text_lower, _add)
    _extract_person_title(text, text_lower, _add)
    _extract_book_movie(text, text_lower, _add)
    _extract_currency(text, text_lower, _add)
    _extract_capitalized_names(text, text_lower, entities, seen_spans, _add)

    entities.sort(key=lambda e: e.start)
    return entities


def _extract_dictionary(raw: str, lower: str, add) -> None:
    for dict_name, dictionary, entity_type in _DICTIONARIES:
        for term, confidence in dictionary.items():
            idx = lower.find(term)
            if idx != -1:
                raw_token = raw[idx : idx + len(term)]
                actual_end = idx + len(term)
                if (idx == 0 or not raw[idx - 1].isalnum()) and (
                    actual_end >= len(raw) or not raw[actual_end].isalnum()
                ):
                    add(
                        Entity(
                            text=raw_token,
                            entity_type=entity_type,
                            normalized=term,
                            confidence=confidence,
                            start=idx,
                            end=actual_end,
                            metadata={"dict": dict_name},
                        )
                    )


def _extract_regex(raw: str, lower: str, add) -> None:
    for pattern, entity_type, confidence, _normalize_fn in [
        (_URL_PATTERN, "URL", 1.0, None),
        (_EMAIL_PATTERN, "EMAIL", 1.0, None),
        (_FILE_PATTERN, "FILE", 0.9, None),
        (_PERCENTAGE_PATTERN, "PERCENTAGE", 1.0, None),
        (_VERSION_PATTERN, "VERSION", 0.85, None),
        (_TIME_PATTERN, "TIME", 0.9, None),
        (_CURRENCY_SYMBOLS, "CURRENCY", 1.0, None),
    ]:
        for match in pattern.finditer(raw):
            start, end = match.start(), match.end()
            add(
                Entity(
                    text=raw[start:end],
                    entity_type=entity_type,
                    normalized=raw[start:end].lower(),
                    confidence=confidence,
                    start=start,
                    end=end,
                )
            )

    for match in _YEAR_PATTERN.finditer(raw):
        start, end = match.start(), match.end()
        add(
            Entity(
                text=raw[start:end],
                entity_type="YEAR",
                normalized=raw[start:end],
                confidence=0.9,
                start=start,
                end=end,
            )
        )

    for match in _NUMBER_PATTERN.finditer(raw):
        start, end = match.start(), match.end()
        val = raw[start:end]
        try:
            if int(val) > 10000:
                continue
        except ValueError:
            continue
        text_before = raw[:start].rstrip()
        if text_before.endswith((":", "version", "v", ".")):
            continue
        add(
            Entity(
                text=val,
                entity_type="NUMBER",
                normalized=val,
                confidence=0.7,
                start=start,
                end=end,
            )
        )


def _extract_organization(raw: str, lower: str, add) -> None:
    org_seen: set[tuple[int, int]] = set()
    for keyword in _ORGANIZATION_KEYWORDS:
        kw_pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        for kw_match in kw_pattern.finditer(lower):
            kw_start = kw_match.start()
            kw_end = kw_match.end()

            pos = kw_start - 1
            while pos >= 0 and raw[pos] in (" ", "\t"):
                pos -= 1
            if pos < 0:
                continue

            first_start = len(raw)
            while pos >= 0:
                while pos >= 0 and raw[pos] in (" ", "\t"):
                    pos -= 1
                if pos < 0:
                    break
                token_end = pos + 1
                while pos >= 0 and (raw[pos].isalnum() or raw[pos] in ("'", ".", "-")):
                    pos -= 1
                token_start = pos + 1
                token = raw[token_start:token_end]
                if not token or len(token) <= 1:
                    break
                if token[0].isupper():
                    first_start = token_start
                else:
                    break

            if first_start >= kw_start:
                continue

            span = (first_start, kw_end)
            if span in org_seen:
                continue
            org_seen.add(span)
            add(
                Entity(
                    text=raw[first_start:kw_end],
                    entity_type="ORGANIZATION",
                    normalized=lower[first_start:kw_end],
                    confidence=0.85,
                    start=first_start,
                    end=kw_end,
                )
            )


def _extract_person_title(raw: str, lower: str, add) -> None:
    for match in _PERSON_TITLE_PATTERN.finditer(raw):
        start, end = match.start(), match.end()
        name = match.group(1)
        if name.lower() not in ("a", "an", "the", "is", "it", "this", "that"):
            add(
                Entity(
                    text=match.group(0),
                    entity_type="PERSON",
                    normalized=name.lower(),
                    confidence=0.8,
                    start=start,
                    end=end,
                )
            )


def _extract_book_movie(raw: str, lower: str, add) -> None:
    for match in _BOOK_MOVIE_PATTERN.finditer(lower):
        title = match.group(1) or match.group(2) or match.group(3) or match.group(4)
        if title and len(title) > 1:
            category_word = raw[match.start() : match.start() + match.group(0).find(title.strip())].strip().lower()
            etype = "BOOK" if any(w in category_word for w in ("book", "novel", "play")) else "MOVIE"
            add(
                Entity(
                    text=title.strip(),
                    entity_type=etype,
                    normalized=title.strip().lower(),
                    confidence=0.7,
                    start=raw.lower().find(title.strip().lower()),
                    end=raw.lower().find(title.strip().lower()) + len(title.strip()),
                )
            )


def _extract_currency(raw: str, lower: str, add) -> None:
    for match in _CURRENCY_PATTERN.finditer(raw):
        start, end = match.start(), match.end()
        add(
            Entity(
                text=raw[start:end],
                entity_type="CURRENCY",
                normalized=raw[start:end].lower(),
                confidence=0.9,
                start=start,
                end=end,
            )
        )


def _extract_capitalized_names(raw: str, lower: str, entities: list[Entity], seen_spans: set, add) -> None:
    existing_texts = {e.text.lower() for e in entities}
    existing_spans = set(seen_spans)
    for e in entities:
        existing_spans.add((e.start, e.end))
    for match in _CAPITALIZED_NAME.finditer(raw):
        start, end = match.start(), match.end()
        if any(s < end and e > start for s, e in existing_spans):
            continue
        token = raw[start:end].strip()
        token_lower = token.lower()
        if token_lower in existing_texts:
            continue
        if len(token.split()) > 3:
            continue
        if token_lower in ("the", "this", "that", "what", "how", "why", "when", "where"):
            continue
        if raw[start:end].isupper():
            continue
        add(
            Entity(
                text=token,
                entity_type="OTHER",
                normalized=token_lower,
                confidence=0.5,
                start=start,
                end=end,
            )
        )
