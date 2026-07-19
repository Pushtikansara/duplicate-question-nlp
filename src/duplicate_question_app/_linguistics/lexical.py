"""Lexical Penalty Engine — penalizes duplicate probability when questions have
different nouns, verbs, named entities, software names, programming languages, or products.

This module provides fine-grained lexical analysis to prevent false positives
on semantically different but lexically similar questions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
from enum import Enum


class PenaltyType(Enum):
    DIFFERENT_NOUNS = "different_nouns"
    DIFFERENT_VERBS = "different_verbs"
    DIFFERENT_ENTITIES = "different_entities"
    DIFFERENT_SOFTWARE = "different_software"
    DIFFERENT_LANGUAGES = "different_languages"
    DIFFERENT_PRODUCTS = "different_products"
    DIFFERENT_VERSIONS = "different_versions"
    DIFFERENT_NUMBERS = "different_numbers"
    LOW_OVERLAP = "low_overlap"


@dataclass
class LexicalPenaltyResult:
    """Result of lexical penalty analysis."""
    total_penalty: float  # 0-1, applied to duplicate probability
    penalties: Dict[PenaltyType, float]
    details: List[str]
    q1_tokens: Dict[str, Set[str]]
    q2_tokens: Dict[str, Set[str]]
    overlap_scores: Dict[str, float]


# POS tagging patterns (simple heuristic-based)
_NOUN_SUFFIXES: Set[str] = {
    "tion", "sion", "ment", "ness", "ity", "ty", "ance", "ence", "ence",
    "er", "or", "ist", "ant", "ent", "ee", "ism", "ship", "hood", "dom",
    "age", "al", "ance", "ence", "ery", "ry", "cy", "sy", "ty", "ure",
}

_VERB_SUFFIXES: Set[str] = {
    "ize", "ise", "ate", "ify", "fy", "en", "ed", "ing", "s", "es",
}

# Programming language keywords
_PROGRAMMING_LANGUAGES: Set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", "csharp",
    "go", "golang", "rust", "swift", "kotlin", "scala", "ruby", "php",
    "perl", "r", "matlab", "julia", "dart", "lua", "haskell", "clojure",
    "erlang", "elixir", "f#", "vb.net", "objective-c", "assembly", "asm",
    "sql", "html", "css", "bash", "powershell", "shell", "awk", "sed",
}

# Software/framework names
_SOFTWARE_NAMES: Set[str] = {
    "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
    "gitlab", "github", "bitbucket", "jira", "confluence", "vscode",
    "intellij", "pycharm", "webstorm", "clion", "rider", "goland",
    "tensorflow", "pytorch", "keras", "jax", "scikit-learn", "xgboost",
    "lightgbm", "catboost", "huggingface", "transformers", "langchain",
    "llamaindex", "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    "plotly", "bokeh", "requests", "httpx", "aiohttp", "asyncio", "celery",
    "redis", "sqlalchemy", "peewee", "tortoise-orm", "prisma", "typeorm",
    "sequelize", "mongoose", "graphql", "apollo", "grpc", "protobuf",
    "kafka", "rabbitmq", "prometheus", "grafana", "elk", "elasticsearch",
    "logstash", "kibana", "jenkins", "gitlab ci", "github actions",
    "circleci", "travis", "argo", "tekton", "vagrant", "helm", "istio",
    "linkerd", "consul", "vault", "nomad", "packer", "aws", "gcp", "azure",
    "digitalocean", "linode", "vultr", "heroku", "render", "vercel", "netlify",
    "cloudflare", "mongodb", "postgresql", "mysql", "mariadb", "sqlite",
    "cassandra", "dynamodb", "redis", "elasticsearch", "opensearch",
    "meilisearch", "typesense", "clickhouse", "snowflake", "bigquery",
    "redshift", "databricks", "spark", "flink", "kafka streams", "airflow",
    "prefect", "dagster", "luigi", "dbt", "fivetran", "airbyte", "stitch",
    "cuda", "cudnn", "tensorrt", "onnx", "onnxruntime", "openvino", "tflite",
    "coreml", "mps", "rocm", "hip", "oneapi", "mkl", "mkl-dnn", "blas", "lapack",
}

# Product names
_PRODUCT_NAMES: Set[str] = {
    "vscode", "visual studio", "intellij", "pycharm", "webstorm", "clion",
    "rider", "goland", "datagrip", "rubymine", "phpstorm", "rider", "fleet",
    "vim", "neovim", "emacs", "spacemacs", "doom emacs", "sublime text",
    "atom", "brackets", "postman", "insomnia", "hoppscotch", "bruno", "httpie",
    "curl", "wget", "terraform", "pulumi", "crossplane", "kustomize", "kpt",
    "helm", "argocd", "flux", "tekton", "jira", "confluence", "notion",
    "linear", "clickup", "asana", "trello", "monday", "slack", "discord",
    "teams", "zoom", "meet", "webex", "mattermost", "rocketchat",
}

# Operating systems
_OPERATING_SYSTEMS: Set[str] = {
    "ubuntu", "debian", "fedora", "centos", "rhel", "arch", "manjaro",
    "opensuse", "alpine", "linux", "windows", "macos", "mac os x", "osx",
    "darwin", "freebsd", "openbsd", "netbsd", "android", "ios", "ipados",
    "watchos", "tvos", "wsl", "wsl2", "cygwin", "mingw", "msys2",
}

# Company names
_COMPANIES: Set[str] = {
    "google", "microsoft", "apple", "amazon", "meta", "facebook", "netflix",
    "uber", "airbnb", "twitter", "x.com", "github", "gitlab", "bitbucket",
    "atlassian", "jetbrains", "adobe", "salesforce", "oracle", "ibm",
    "intel", "amd", "nvidia", "qualcomm", "cisco", "vmware", "red hat",
    "canonical", "docker", "hashicorp", "mongodb", "redis", "elastic",
    "confluent", "databricks", "snowflake", "stripe", "twilio", "sendgrid",
    "mailgun", "postmark", "vercel", "netlify", "cloudflare", "digitalocean",
    "linode", "vultr", "heroku", "render", "railway", "fly.io", "planetscale",
    "supabase", "firebase",
}


@dataclass
class TokenAnalysis:
    """Token analysis for a single question."""
    nouns: Set[str]
    verbs: Set[str]
    entities: Set[str]
    software: Set[str]
    languages: Set[str]
    products: Set[str]
    versions: Set[str]
    numbers: Set[str]
    all_tokens: Set[str]


def extract_tokens(text: str) -> TokenAnalysis:
    """Extract different token types from text."""
    text_lower = text.lower()
    words = re.findall(r"\b\w+(?:[-']\w+)*\b", text_lower)

    # Simple noun/verb detection using suffixes
    nouns = set()
    verbs = set()

    for word in words:
        # Check noun suffixes
        for suffix in _NOUN_SUFFIXES:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                nouns.add(word)
                break
        # Check verb suffixes
        for suffix in _VERB_SUFFIXES:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                verbs.add(word)
                break

    # Extract known entities
    entities = set()
    software = set()
    languages = set()
    products = set()

    for word in words:
        if word in _SOFTWARE_NAMES:
            software.add(word)
        if word in _PROGRAMMING_LANGUAGES:
            languages.add(word)
        if word in _PRODUCT_NAMES:
            products.add(word)
        if word in _OPERATING_SYSTEMS:
            entities.add(word)
        if word in _COMPANIES:
            entities.add(word)

    # Version numbers
    version_pattern = re.compile(r"\b\d+(?:\.\d+){1,3}(?:[-_](?:alpha|beta|rc|dev|stable|lts))?\b")
    versions = set(version_pattern.findall(text_lower))

    # Numbers
    number_pattern = re.compile(r"\b\d+(?:[.,]\d+)?\b")
    numbers = set(number_pattern.findall(text_lower))

    return TokenAnalysis(
        nouns=nouns,
        verbs=verbs,
        entities=entities,
        software=software,
        languages=languages,
        products=products,
        versions=versions,
        numbers=numbers,
        all_tokens=set(words),
    )


def compute_overlap(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard overlap between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0


def compute_lexical_penalty(q1: str, q2: str) -> LexicalPenaltyResult:
    """Compute lexical penalty for a question pair."""
    t1 = extract_tokens(q1)
    t2 = extract_tokens(q2)

    penalties: Dict[PenaltyType, float] = {}
    details = []

    # 1. Noun overlap
    noun_overlap = compute_overlap(t1.nouns, t2.nouns)
    if noun_overlap < 0.3 and (t1.nouns or t2.nouns):
        penalties[PenaltyType.DIFFERENT_NOUNS] = 0.15 * (1.0 - noun_overlap)
        details.append(f"Low noun overlap ({noun_overlap:.2f}): Q1={t1.nouns}, Q2={t2.nouns}")

    # 2. Verb overlap
    verb_overlap = compute_overlap(t1.verbs, t2.verbs)
    if verb_overlap < 0.3 and (t1.verbs or t2.verbs):
        penalties[PenaltyType.DIFFERENT_VERBS] = 0.10 * (1.0 - verb_overlap)
        details.append(f"Low verb overlap ({verb_overlap:.2f}): Q1={t1.verbs}, Q2={t2.verbs}")

    # 3. Entity mismatch
    entity_overlap = compute_overlap(t1.entities, t2.entities)
    if t1.entities and t2.entities and entity_overlap == 0:
        penalties[PenaltyType.DIFFERENT_ENTITIES] = 0.25
        details.append(f"Different entities: Q1={t1.entities}, Q2={t2.entities}")

    # 4. Software name mismatch
    software_overlap = compute_overlap(t1.software, t2.software)
    if t1.software and t2.software and software_overlap == 0:
        penalties[PenaltyType.DIFFERENT_SOFTWARE] = 0.30
        details.append(f"Different software: Q1={t1.software}, Q2={t2.software}")

    # 5. Programming language mismatch
    lang_overlap = compute_overlap(t1.languages, t2.languages)
    if t1.languages and t2.languages and lang_overlap == 0:
        penalties[PenaltyType.DIFFERENT_LANGUAGES] = 0.35
        details.append(f"Different languages: Q1={t1.languages}, Q2={t2.languages}")

    # 6. Product mismatch
    product_overlap = compute_overlap(t1.products, t2.products)
    if t1.products and t2.products and product_overlap == 0:
        penalties[PenaltyType.DIFFERENT_PRODUCTS] = 0.20
        details.append(f"Different products: Q1={t1.products}, Q2={t2.products}")

    # 7. Version mismatch
    version_overlap = compute_overlap(t1.versions, t2.versions)
    if t1.versions and t2.versions and version_overlap == 0:
        penalties[PenaltyType.DIFFERENT_VERSIONS] = 0.15
        details.append(f"Different versions: Q1={t1.versions}, Q2={t2.versions}")

    # 8. Number mismatch
    number_overlap = compute_overlap(t1.numbers, t2.numbers)
    if t1.numbers and t2.numbers and number_overlap == 0:
        penalties[PenaltyType.DIFFERENT_NUMBERS] = 0.10
        details.append(f"Different numbers: Q1={t1.numbers}, Q2={t2.numbers}")

    # 9. Overall token overlap
    total_overlap = compute_overlap(t1.all_tokens, t2.all_tokens)
    if total_overlap < 0.2:
        penalties[PenaltyType.LOW_OVERLAP] = 0.20 * (1.0 - total_overlap)
        details.append(f"Very low overall token overlap ({total_overlap:.2f})")

    # Compute total penalty (capped at 0.8)
    total_penalty = min(0.8, sum(penalties.values()))

    return LexicalPenaltyResult(
        total_penalty=total_penalty,
        penalties=penalties,
        details=details,
        q1_tokens={
            "nouns": t1.nouns, "verbs": t1.verbs, "entities": t1.entities,
            "software": t1.software, "languages": t1.languages,
            "products": t1.products, "versions": t1.versions, "numbers": t1.numbers,
        },
        q2_tokens={
            "nouns": t2.nouns, "verbs": t2.verbs, "entities": t2.entities,
            "software": t2.software, "languages": t2.languages,
            "products": t2.products, "versions": t2.versions, "numbers": t2.numbers,
        },
        overlap_scores={
            "noun": noun_overlap, "verb": verb_overlap, "entity": entity_overlap,
            "software": software_overlap, "language": lang_overlap,
            "product": product_overlap, "version": version_overlap,
            "number": number_overlap, "total": total_overlap,
        },
    )


def get_lexical_penalty(q1: str, q2: str) -> Tuple[float, str]:
    """Get lexical penalty for ensemble scoring."""
    result = compute_lexical_penalty(q1, q2)
    if result.total_penalty > 0:
        return result.total_penalty, "; ".join(result.details)
    return 0.0, "No significant lexical mismatch"