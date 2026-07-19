"""Entity Detection Engine — extracts programming languages, frameworks, operating systems,
companies, people, technologies, versions, numbers, dates, products, countries, cities,
currencies, and units from questions.

If important entities differ between question pairs, apply a penalty to duplicate probability.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

# Entity dictionaries for exact matching
_PROGRAMMING_LANGUAGES: set[str] = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "c",
    "go",
    "rust",
    "swift",
    "kotlin",
    "scala",
    "ruby",
    "php",
    "perl",
    "r",
    "matlab",
    "julia",
    "dart",
    "lua",
    "haskell",
    "clojure",
    "erlang",
    "elixir",
    "f#",
    "vb.net",
    "objective-c",
    "assembly",
    "sql",
    "html",
    "css",
    "bash",
    "powershell",
    "sas",
    "stata",
    "spss",
}

_FRAMEWORKS: set[str] = {
    "django",
    "flask",
    "fastapi",
    "spring",
    "spring boot",
    "express",
    "nestjs",
    "koa",
    "react",
    "vue",
    "angular",
    "svelte",
    "next.js",
    "nuxt",
    "gatsby",
    "remix",
    "tensorflow",
    "pytorch",
    "keras",
    "jax",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "catboost",
    "huggingface",
    "transformers",
    "langchain",
    "llamaindex",
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "plotly",
    "bokeh",
    "requests",
    "httpx",
    "aiohttp",
    "asyncio",
    "celery",
    "redis",
    "sqlalchemy",
    "peewee",
    "tortoise-orm",
    "prisma",
    "typeorm",
    "sequelize",
    "mongoose",
    "graphql",
    "apollo",
    "relay",
    "grpc",
    "protobuf",
    "kafka",
    "rabbitmq",
    "docker",
    "kubernetes",
    "k8s",
    "helm",
    "terraform",
    "ansible",
    "prometheus",
    "grafana",
    "elk",
    "elastic",
    "logstash",
    "kibana",
    "jenkins",
    "gitlab ci",
    "github actions",
    "circleci",
    "travis",
    "argo",
    "tekton",
    "vagrant",
}

_OPERATING_SYSTEMS: set[str] = {
    "ubuntu",
    "debian",
    "fedora",
    "centos",
    "rhel",
    "arch",
    "manjaro",
    "opensuse",
    "alpine",
    "linux",
    "windows",
    "macos",
    "mac os x",
    "osx",
    "darwin",
    "freebsd",
    "openbsd",
    "netbsd",
    "android",
    "ios",
    "ipados",
    "watchos",
    "tvos",
    "wsl",
    "wsl2",
    "cygwin",
    "mingw",
    "msys2",
}

_COMPANIES: set[str] = {
    "google",
    "microsoft",
    "apple",
    "amazon",
    "meta",
    "facebook",
    "netflix",
    "uber",
    "airbnb",
    "twitter",
    "x.com",
    "github",
    "gitlab",
    "bitbucket",
    "atlassian",
    "jetbrains",
    "adobe",
    "salesforce",
    "oracle",
    "ibm",
    "intel",
    "amd",
    "nvidia",
    "qualcomm",
    "cisco",
    "vmware",
    "red hat",
    "canonical",
    "docker",
    "hashicorp",
    "mongodb",
    "redis",
    "elastic",
    "confluent",
    "databricks",
    "snowflake",
    "stripe",
    "twilio",
    "sendgrid",
    "mailgun",
    "postmark",
    "vercel",
    "netlify",
    "cloudflare",
    "aws",
    "gcp",
    "azure",
    "digitalocean",
    "linode",
    "vultr",
    "heroku",
    "render",
    "railway",
    "fly.io",
    "planetscale",
    "supabase",
    "firebase",
}

_TECHNOLOGIES: set[str] = {
    "git",
    "github",
    "gitlab",
    "bitbucket",
    "svn",
    "mercurial",
    "perforce",
    "docker",
    "podman",
    "containerd",
    "kubernetes",
    "k8s",
    "helm",
    "istio",
    "linkerd",
    "consul",
    "vault",
    "nomad",
    "terraform",
    "packer",
    "vagrant",
    "ansible",
    "chef",
    "puppet",
    "saltstack",
    "jenkins",
    "gitlab ci",
    "github actions",
    "circleci",
    "travis",
    "bamboo",
    "teamcity",
    "argo",
    "tekton",
    "flux",
    "argo cd",
    "prometheus",
    "grafana",
    "loki",
    "tempo",
    "jaeger",
    "zipkin",
    "elk",
    "elastic",
    "logstash",
    "kibana",
    "filebeat",
    "metricbeat",
    "packetbeat",
    "auditbeat",
    "kafka",
    "rabbitmq",
    "pulsar",
    "nats",
    "redis",
    "memcached",
    "etcd",
    "postgresql",
    "mysql",
    "mariadb",
    "sqlite",
    "mongodb",
    "cassandra",
    "dynamodb",
    "elasticsearch",
    "opensearch",
    "meilisearch",
    "typesense",
    "clickhouse",
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    "spark",
    "flink",
    "kafka streams",
    "airflow",
    "prefect",
    "dagster",
    "luigi",
    "dbt",
    "fivetran",
    "airbyte",
    "stitch",
    "cuda",
    "cudnn",
    "tensorrt",
    "onnx",
    "onnxruntime",
    "openvino",
    "tflite",
    "coreml",
    "mps",
    "rocm",
    "hip",
    "oneapi",
    "mkl",
    "mkl-dnn",
    "blas",
    "lapack",
}

_PRODUCTS: set[str] = {
    "vscode",
    "visual studio",
    "intellij",
    "pycharm",
    "webstorm",
    "clion",
    "rider",
    "goland",
    "datagrip",
    "rubymine",
    "phpstorm",
    "fleet",
    "vim",
    "neovim",
    "emacs",
    "spacemacs",
    "doom emacs",
    "sublime text",
    "atom",
    "brackets",
    "postman",
    "insomnia",
    "hoppscotch",
    "bruno",
    "httpie",
    "curl",
    "wget",
    "terraform",
    "pulumi",
    "crossplane",
    "kustomize",
    "kpt",
    "helm",
    "argocd",
    "flux",
    "tekton",
    "jenkins",
    "gitlab",
    "github",
    "bitbucket",
    "gitea",
    "jira",
    "confluence",
    "notion",
    "linear",
    "clickup",
    "asana",
    "trello",
    "monday",
    "slack",
    "discord",
    "teams",
    "zoom",
    "meet",
    "webex",
    "mattermost",
    "rocketchat",
}

_COUNTRIES: set[str] = {
    "usa",
    "united states",
    "america",
    "uk",
    "united kingdom",
    "britain",
    "england",
    "canada",
    "australia",
    "germany",
    "france",
    "italy",
    "spain",
    "netherlands",
    "belgium",
    "switzerland",
    "austria",
    "sweden",
    "norway",
    "denmark",
    "finland",
    "poland",
    "czech republic",
    "hungary",
    "romania",
    "bulgaria",
    "croatia",
    "serbia",
    "greece",
    "portugal",
    "ireland",
    "new zealand",
    "singapore",
    "japan",
    "china",
    "india",
    "brazil",
    "mexico",
    "argentina",
    "chile",
    "colombia",
    "peru",
    "korea",
    "south korea",
    "north korea",
    "taiwan",
    "hong kong",
    "israel",
    "uae",
    "saudi arabia",
    "turkey",
    "russia",
    "ukraine",
    "belarus",
    "kazakhstan",
    "uzbekistan",
    "vietnam",
    "thailand",
    "malaysia",
    "indonesia",
    "philippines",
    "pakistan",
    "bangladesh",
    "nigeria",
    "south africa",
    "egypt",
    "kenya",
    "morocco",
    "tunisia",
    "ghana",
}

_CITIES: set[str] = {
    "new york",
    "los angeles",
    "chicago",
    "houston",
    "phoenix",
    "philadelphia",
    "san antonio",
    "san diego",
    "dallas",
    "san jose",
    "austin",
    "jacksonville",
    "fort worth",
    "columbus",
    "charlotte",
    "san francisco",
    "seattle",
    "denver",
    "washington dc",
    "boston",
    "el paso",
    "detroit",
    "nashville",
    "portland",
    "oklahoma city",
    "las vegas",
    "memphis",
    "louisville",
    "baltimore",
    "milwaukee",
    "albuquerque",
    "tucson",
    "fresno",
    "sacramento",
    "mesa",
    "kansas city",
    "atlanta",
    "long beach",
    "colorado springs",
    "raleigh",
    "miami",
    "virginia beach",
    "omaha",
    "oakland",
    "minneapolis",
    "tulsa",
    "arlington",
    "tampa",
    "new orleans",
    "london",
    "birmingham",
    "manchester",
    "glasgow",
    "liverpool",
    "leeds",
    "sheffield",
    "edinburgh",
    "bristol",
    "cardiff",
    "belfast",
    "newcastle",
    "nottingham",
    "paris",
    "marseille",
    "lyon",
    "toulouse",
    "nice",
    "nantes",
    "strasbourg",
    "montpellier",
    "bordeaux",
    "lille",
    "rennes",
    "reims",
    "le havre",
    "saint-etienne",
    "tokyo",
    "yokohama",
    "osaka",
    "nagoya",
    "sapporo",
    "fukuoka",
    "kobe",
    "kyoto",
    "kawasaki",
    "saitama",
    "hiroshima",
    "sendai",
    "kitakyushu",
    "chiba",
    "sakai",
}

_CURRENCIES: set[str] = {
    "usd",
    "dollar",
    "dollars",
    "eur",
    "euro",
    "euros",
    "gbp",
    "pound",
    "pounds",
    "jpy",
    "yen",
    "cny",
    "yuan",
    "rmb",
    "inr",
    "rupee",
    "rupees",
    "cad",
    "aud",
    "chf",
    "sek",
    "nok",
    "dkk",
    "pln",
    "czk",
    "huf",
    "ron",
    "bgn",
    "hrk",
    "rub",
    "try",
    "ils",
    "aed",
    "sar",
    "qar",
    "kwd",
    "bhd",
    "omr",
    "jod",
    "lbp",
    "egp",
    "zar",
    "ngn",
    "kes",
    "ghs",
    "tzs",
    "ugx",
    "rwf",
    "zmw",
    "mwk",
    "bwp",
    "nad",
}

_UNITS: set[str] = {
    "gb",
    "mb",
    "kb",
    "tb",
    "pb",
    "ghz",
    "mhz",
    "khz",
    "ms",
    "us",
    "ns",
    "s",
    "m",
    "h",
    "px",
    "dpi",
    "ppi",
    "fps",
    "hz",
    "rpm",
    "bps",
    "kbps",
    "mbps",
    "gbps",
    "tbps",
    "c",
    "f",
    "k",
    "v",
    "a",
    "w",
    "wh",
    "kwh",
    "mah",
    "ah",
    "ohm",
    "farad",
    "henry",
    "tesla",
    "gauss",
    "weber",
    "lumen",
    "lux",
    "candela",
    "diopter",
}

# Regex patterns for versions, numbers, dates
_VERSION_PATTERN = re.compile(r"\b\d+(?:\.\d+){1,3}(?:[-_](?:alpha|beta|rc|dev|stable|lts))?\b", re.IGNORECASE)
_DATE_PATTERN = re.compile(
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)
_NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")


@dataclass
class EntityMatch:
    """A single detected entity."""

    entity_type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class EntityDetectionResult:
    """Result of entity detection for a question pair."""

    q1_entities: list[EntityMatch]
    q2_entities: list[EntityMatch]
    entity_overlap: dict[str, set[str]]  # type -> shared entities
    entity_mismatch: dict[str, tuple[set[str], set[str]]]  # type -> (q1_only, q2_only)
    mismatch_penalty: float
    penalty_details: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "q1_entities": [{"type": e.entity_type, "value": e.value} for e in self.q1_entities],
            "q2_entities": [{"type": e.entity_type, "value": e.value} for e in self.q2_entities],
            "entity_overlap": {k: list(v) for k, v in self.entity_overlap.items()},
            "entity_mismatch": {k: {"q1": list(v[0]), "q2": list(v[1])} for k, v in self.entity_mismatch.items()},
            "mismatch_penalty": self.mismatch_penalty,
            "penalty_details": self.penalty_details,
        }


def _extract_entities_from_text(text: str, entity_dict: set[str], entity_type: str) -> list[EntityMatch]:
    """Extract entities of a specific type from text using exact matching."""
    matches = []
    text_lower = text.lower()
    for entity in entity_dict:
        # Use word boundaries for matching
        pattern = r"\b" + re.escape(entity) + r"\b"
        for match in re.finditer(pattern, text_lower):
            matches.append(
                EntityMatch(entity_type=entity_type, value=entity, start=match.start(), end=match.end(), confidence=1.0)
            )
    return matches


def _extract_versions(text: str) -> list[EntityMatch]:
    """Extract version numbers from text."""
    matches = []
    for match in _VERSION_PATTERN.finditer(text):
        matches.append(
            EntityMatch(
                entity_type="version", value=match.group(), start=match.start(), end=match.end(), confidence=0.9
            )
        )
    return matches


def _extract_dates(text: str) -> list[EntityMatch]:
    """Extract dates from text."""
    matches = []
    for match in _DATE_PATTERN.finditer(text):
        matches.append(
            EntityMatch(entity_type="date", value=match.group(), start=match.start(), end=match.end(), confidence=0.8)
        )
    return matches


def _extract_numbers(text: str) -> list[EntityMatch]:
    """Extract numbers from text."""
    matches = []
    for match in _NUMBER_PATTERN.finditer(text):
        val = match.group()
        # Filter out very short numbers that are likely not meaningful
        if len(val) >= 2 or val.isdigit():
            matches.append(
                EntityMatch(entity_type="number", value=val, start=match.start(), end=match.end(), confidence=0.5)
            )
    return matches


def detect_entities(text: str) -> list[EntityMatch]:
    """Detect all entities in a text."""
    entities = []

    entities.extend(_extract_entities_from_text(text, _PROGRAMMING_LANGUAGES, "programming_language"))
    entities.extend(_extract_entities_from_text(text, _FRAMEWORKS, "framework"))
    entities.extend(_extract_entities_from_text(text, _OPERATING_SYSTEMS, "operating_system"))
    entities.extend(_extract_entities_from_text(text, _COMPANIES, "company"))
    entities.extend(_extract_entities_from_text(text, _TECHNOLOGIES, "technology"))
    entities.extend(_extract_entities_from_text(text, _PRODUCTS, "product"))
    entities.extend(_extract_entities_from_text(text, _COUNTRIES, "country"))
    entities.extend(_extract_entities_from_text(text, _CITIES, "city"))
    entities.extend(_extract_entities_from_text(text, _CURRENCIES, "currency"))
    entities.extend(_extract_entities_from_text(text, _UNITS, "unit"))

    entities.extend(_extract_versions(text))
    entities.extend(_extract_dates(text))
    entities.extend(_extract_numbers(text))

    # Sort by position
    entities.sort(key=lambda e: e.start)
    return entities


def compute_entity_mismatch(
    q1_entities: list[EntityMatch],
    q2_entities: list[EntityMatch],
) -> EntityDetectionResult:
    """Compute entity overlap and mismatch between two questions."""
    # Group entities by type
    q1_by_type: dict[str, set[str]] = defaultdict(set)
    q2_by_type: dict[str, set[str]] = defaultdict(set)

    for e in q1_entities:
        q1_by_type[e.entity_type].add(e.value.lower())
    for e in q2_entities:
        q2_by_type[e.entity_type].add(e.value.lower())

    all_types = set(q1_by_type.keys()) | set(q2_by_type.keys())

    entity_overlap: dict[str, set[str]] = {}
    entity_mismatch: dict[str, tuple[set[str], set[str]]] = {}

    penalty_details = []
    total_penalty = 0.0

    # Weight for each entity type (importance for duplicate detection)
    type_weights = {
        "programming_language": 0.25,
        "framework": 0.20,
        "operating_system": 0.15,
        "company": 0.10,
        "technology": 0.15,
        "product": 0.10,
        "version": 0.15,
        "country": 0.05,
        "city": 0.03,
        "currency": 0.03,
        "unit": 0.03,
        "number": 0.02,
        "date": 0.02,
    }

    for etype in all_types:
        q1_set = q1_by_type.get(etype, set())
        q2_set = q2_by_type.get(etype, set())

        overlap = q1_set & q2_set
        q1_only = q1_set - q2_set
        q2_only = q2_set - q1_set

        if overlap:
            entity_overlap[etype] = overlap
        if q1_only or q2_only:
            entity_mismatch[etype] = (q1_only, q2_only)

        # Apply penalty for mismatched important entities
        if q1_only or q2_only:
            weight = type_weights.get(etype, 0.05)
            # Only penalize if both questions have entities of this type but they differ
            if q1_set and q2_set and not overlap:
                penalty = weight * 1.0
                total_penalty += penalty
                penalty_details.append(f"{etype}: Q1={sorted(q1_only)}, Q2={sorted(q2_only)} (penalty: {penalty:.2f})")
            elif q1_set and not q2_set:
                # Q1 has entity type, Q2 doesn't - smaller penalty
                penalty = weight * 0.5
                total_penalty += penalty
                penalty_details.append(f"{etype}: Q1={sorted(q1_set)}, Q2=none (penalty: {penalty:.2f})")
            elif q2_set and not q1_set:
                penalty = weight * 0.5
                total_penalty += penalty
                penalty_details.append(f"{etype}: Q1=none, Q2={sorted(q2_set)} (penalty: {penalty:.2f})")

    # Cap penalty at 0.8 (80% reduction)
    total_penalty = min(0.8, total_penalty)

    return EntityDetectionResult(
        q1_entities=q1_entities,
        q2_entities=q2_entities,
        entity_overlap=entity_overlap,
        entity_mismatch=entity_mismatch,
        mismatch_penalty=total_penalty,
        penalty_details=penalty_details,
    )


def analyze_entity_mismatch(q1: str, q2: str) -> EntityDetectionResult:
    """Main entry point: analyze entity mismatch between two questions."""
    q1_entities = detect_entities(q1)
    q2_entities = detect_entities(q2)
    return compute_entity_mismatch(q1_entities, q2_entities)


def get_entity_penalty(q1: str, q2: str) -> tuple[float, list[str]]:
    """Get entity mismatch penalty and details for a question pair."""
    result = analyze_entity_mismatch(q1, q2)
    return result.mismatch_penalty, result.penalty_details
