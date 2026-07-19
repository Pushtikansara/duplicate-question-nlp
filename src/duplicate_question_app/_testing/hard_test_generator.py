"""Hard Test Dataset Generator — creates 1000+ extremely difficult question pairs.

Categories:
- Programming (languages, frameworks, versions)
- Linux (commands, distros, package managers)
- AI/ML (models, frameworks, concepts)
- Cloud (AWS, GCP, Azure, services)
- Networking (protocols, tools, concepts)
- Medicine (terms, treatments, diagnostics)
- Finance (instruments, regulations, metrics)
- Math (theorems, formulas, concepts)
- General Knowledge
- Legal (terms, jurisdictions, procedures)
- Education (pedagogy, systems, degrees)
- Security (vulnerabilities, tools, concepts)

Each category includes:
- Abbreviations (AI vs Artificial Intelligence)
- Synonyms (learn vs study, install vs setup)
- Negation (can I install vs can I uninstall)
- Paraphrases (how to X vs tutorial for X)
- Entity swaps (Python vs Java, AWS vs Azure)
- Contradictions (enable vs disable, before vs after)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from duplicate_question_app._config.logging_setup import get_logger

_logger = get_logger(__name__)


class Category(Enum):
    PROGRAMMING = "programming"
    LINUX = "linux"
    AI_ML = "ai_ml"
    CLOUD = "cloud"
    NETWORKING = "networking"
    MEDICINE = "medicine"
    FINANCE = "finance"
    MATH = "math"
    GENERAL = "general"
    LEGAL = "legal"
    EDUCATION = "education"
    SECURITY = "security"


class DifficultyType(Enum):
    ABBREVIATION = "abbreviation"
    SYNONYM = "synonym"
    NEGATION = "negation"
    PARAPHRASE = "paraphrase"
    ENTITY_SWAP = "entity_swap"
    CONTRADICTION = "contradiction"
    VERSION_MISMATCH = "version_mismatch"
    CONTEXT_SHIFT = "context_shift"
    IMPLICIT_ENTITY = "implicit_entity"
    AMBIGUOUS_INTENT = "ambiguous_intent"


@dataclass
class HardPair:
    """A single hard test pair."""

    q1: str
    q2: str
    true_label: int  # 0 = non-duplicate, 1 = duplicate
    category: Category
    difficulty_types: list[DifficultyType]
    description: str
    expected_fp_reason: str = ""  # Why models might get this wrong


# ============================================================
# TEMPLATE DEFINITIONS PER CATEGORY
# ============================================================

PROGRAMMING_TEMPLATES = {
    "languages": [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C++",
        "C#",
        "Go",
        "Rust",
        "Swift",
        "Kotlin",
        "Ruby",
        "PHP",
        "R",
        "MATLAB",
        "Julia",
        "Dart",
        "Scala",
    ],
    "frameworks": [
        "Django",
        "Flask",
        "FastAPI",
        "Spring Boot",
        "Express",
        "React",
        "Vue",
        "Angular",
        "Svelte",
        "Next.js",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "JAX",
    ],
    "tools": [
        "Git",
        "Docker",
        "Kubernetes",
        "Jenkins",
        "GitLab CI",
        "GitHub Actions",
        "Terraform",
        "Ansible",
        "VS Code",
        "IntelliJ",
        "PyCharm",
    ],
    "concepts": [
        "async/await",
        "decorators",
        "generators",
        "closures",
        "monads",
        "dependency injection",
        "design patterns",
        "microservices",
        "REST API",
        "GraphQL",
    ],
    "package_managers": ["pip", "npm", "yarn", "maven", "gradle", "cargo", "go mod", "composer", "bundler", "nuget"],
}

LINUX_TEMPLATES = {
    "distros": [
        "Ubuntu",
        "Debian",
        "Fedora",
        "CentOS",
        "RHEL",
        "Arch",
        "Manjaro",
        "openSUSE",
        "Alpine",
        "Kali",
        "Mint",
        "Pop!_OS",
    ],
    "commands": [
        "apt",
        "apt-get",
        "dnf",
        "yum",
        "pacman",
        "zypper",
        "apk",
        "systemctl",
        "service",
        "journalctl",
        "grep",
        "sed",
        "awk",
        "find",
        "tar",
        "ssh",
        "scp",
        "rsync",
    ],
    "package_managers": ["apt", "dnf", "pacman", "zypper", "apk", "snap", "flatpak", "brew", "nix", "emerge"],
    "filesystems": ["ext4", "xfs", "btrfs", "zfs", "ntfs", "fat32", "exfat"],
    "kernels": ["Linux 5.x", "Linux 6.x", "Linux LTS", "Zen kernel", "Hardened kernel"],
}

AI_ML_TEMPLATES = {
    "models": [
        "BERT",
        "GPT",
        "T5",
        "BART",
        "RoBERTa",
        "DeBERTa",
        "LLaMA",
        "Mistral",
        "Falcon",
        "Claude",
        "PaLM",
        "Gemini",
    ],
    "frameworks": [
        "TensorFlow",
        "PyTorch",
        "JAX",
        "Keras",
        "Hugging Face Transformers",
        "LangChain",
        "LlamaIndex",
        "MLX",
    ],
    "concepts": [
        "fine-tuning",
        "prompt engineering",
        "RAG",
        "embeddings",
        "vector databases",
        "attention mechanism",
        "transformer architecture",
        "RLHF",
        "LoRA",
        "QLoRA",
    ],
    "hardware": ["GPU", "TPU", "CUDA", "ROCm", "MPS", "CPU inference", "quantization", "distillation"],
    "datasets": ["ImageNet", "COCO", "SQuAD", "GLUE", "SuperGLUE", "WikiText", "Common Crawl", "The Pile", "LAION"],
}

CLOUD_TEMPLATES = {
    "providers": ["AWS", "GCP", "Azure", "DigitalOcean", "Linode", "Vultr", "Hetzner", "Oracle Cloud", "IBM Cloud"],
    "services": [
        "EC2",
        "S3",
        "Lambda",
        "RDS",
        "DynamoDB",
        "CloudRun",
        "Cloud Functions",
        "App Engine",
        "EKS",
        "GKE",
        "AKS",
        "ECS",
        "Fargate",
    ],
    "databases": [
        "RDS",
        "CloudSQL",
        "Cosmos DB",
        "Firestore",
        "DynamoDB",
        "Bigtable",
        "Spanner",
        "Aurora",
        "DocumentDB",
    ],
    "networking": [
        "VPC",
        "Load Balancer",
        "CloudFront",
        "CloudFlare",
        "Route 53",
        "Cloud DNS",
        "API Gateway",
        "Private Link",
    ],
    "iac": ["CloudFormation", "Terraform", "Pulumi", "CDK", "ARM templates", "Deployment Manager"],
}

NETWORKING_TEMPLATES = {
    "protocols": [
        "HTTP/1.1",
        "HTTP/2",
        "HTTP/3",
        "QUIC",
        "TCP",
        "UDP",
        "TLS 1.2",
        "TLS 1.3",
        "WebSocket",
        "gRPC",
        "GraphQL",
        "REST",
        "MQTT",
        "WebRTC",
    ],
    "tools": [
        "curl",
        "wget",
        "httpie",
        "postman",
        "insomnia",
        "wireshark",
        "tcpdump",
        "ngrok",
        "cloudflared",
        "ssh",
        "scp",
        "rsync",
    ],
    "concepts": [
        "DNS",
        "DHCP",
        "NAT",
        "VPN",
        "proxy",
        "reverse proxy",
        "load balancing",
        "CDN",
        "rate limiting",
        "circuit breaker",
        "service mesh",
    ],
    "ports": ["80", "443", "22", "3306", "5432", "6379", "27017", "8080", "8443", "9092"],
}

MEDICINE_TEMPLATES = {
    "conditions": [
        "hypertension",
        "diabetes",
        "asthma",
        "COPD",
        "depression",
        "anxiety",
        "migraine",
        "arthritis",
        "cancer",
        "heart disease",
    ],
    "treatments": [
        "metformin",
        "insulin",
        "lisinopril",
        "amlodipine",
        "atorvastatin",
        "SSRIs",
        "bronchodilators",
        "chemotherapy",
        "immunotherapy",
        "surgery",
    ],
    "diagnostics": [
        "MRI",
        "CT scan",
        "X-ray",
        "ultrasound",
        "blood test",
        "biopsy",
        "ECG",
        "EEG",
        "endoscopy",
        "colonoscopy",
    ],
    "specialties": [
        "cardiology",
        "neurology",
        "oncology",
        "psychiatry",
        "orthopedics",
        "dermatology",
        "gastroenterology",
        "pulmonology",
    ],
    "drug_classes": [
        "ACE inhibitors",
        "beta blockers",
        "statins",
        "SSRIs",
        "SNRIs",
        "anticoagulants",
        "antibiotics",
        "antivirals",
        "corticosteroids",
    ],
}

FINANCE_TEMPLATES = {
    "instruments": [
        "stocks",
        "bonds",
        "ETFs",
        "mutual funds",
        "options",
        "futures",
        "swaps",
        "CDS",
        "MBS",
        "ABS",
        "crypto",
        "forex",
    ],
    "metrics": [
        "P/E ratio",
        "EPS",
        "ROE",
        "ROA",
        "Sharpe ratio",
        "alpha",
        "beta",
        "VaR",
        "duration",
        "convexity",
        "yield curve",
    ],
    "regulations": ["Basel III", "Dodd-Frank", "MiFID II", "GDPR", "SOX", "SEC", "FINRA", "CFTC", "FCA", "BaFin"],
    "markets": ["NYSE", "NASDAQ", "LSE", "TSE", "HKEX", "SSE", "Euronext", "CME", "ICE", "OTC"],
    "concepts": [
        "arbitrage",
        "hedging",
        "diversification",
        "asset allocation",
        "risk parity",
        "factor investing",
        "momentum",
        "value investing",
    ],
}

MATH_TEMPLATES = {
    "theorems": [
        "Pythagorean",
        "Fundamental Theorem of Calculus",
        "Central Limit Theorem",
        "Bayes Theorem",
        "Fermat Last",
        "Godel Incompleteness",
        "Prime Number",
    ],
    "concepts": [
        "derivative",
        "integral",
        "limit",
        "series",
        "convergence",
        "eigenvalue",
        "eigenvector",
        "determinant",
        "matrix",
        "vector space",
        "topology",
        "manifold",
    ],
    "fields": [
        "calculus",
        "linear algebra",
        "probability",
        "statistics",
        "number theory",
        "geometry",
        "analysis",
        "algebra",
        "combinatorics",
        "logic",
    ],
    "notations": [
        "summation",
        "product",
        "integral",
        "derivative",
        "partial derivative",
        "gradient",
        "divergence",
        "curl",
        "laplacian",
    ],
    "problems": [
        "optimization",
        "root finding",
        "differential equations",
        "linear programming",
        "integer programming",
        "graph theory",
        "combinatorial optimization",
    ],
}

GENERAL_TEMPLATES = {
    "countries": [
        "USA",
        "UK",
        "Germany",
        "France",
        "Japan",
        "China",
        "India",
        "Brazil",
        "Canada",
        "Australia",
        "South Korea",
        "Singapore",
    ],
    "cities": [
        "New York",
        "London",
        "Tokyo",
        "Paris",
        "Berlin",
        "Sydney",
        "Toronto",
        "Singapore",
        "Dubai",
        "Hong Kong",
        "Mumbai",
        "Seoul",
    ],
    "currencies": ["USD", "EUR", "GBP", "JPY", "CNY", "INR", "CAD", "AUD", "CHF", "SGD", "KRW", "HKD"],
    "organizations": ["UN", "WHO", "IMF", "World Bank", "WTO", "OECD", "G7", "G20", "NATO", "EU", "ASEAN", "BRICS"],
    "languages": [
        "English",
        "Mandarin",
        "Spanish",
        "Hindi",
        "Arabic",
        "French",
        "Bengali",
        "Russian",
        "Portuguese",
        "Urdu",
        "Japanese",
        "German",
    ],
}

LEGAL_TEMPLATES = {
    "concepts": [
        "contract",
        "tort",
        "liability",
        "negligence",
        "breach",
        "damages",
        "injunction",
        "specific performance",
        "consideration",
        "offer",
        "acceptance",
    ],
    "areas": [
        "corporate law",
        "criminal law",
        "family law",
        "IP law",
        "employment law",
        "tax law",
        "securities law",
        "immigration law",
        "environmental law",
    ],
    "documents": [
        "contract",
        "will",
        "trust",
        "deed",
        "lease",
        "NDA",
        "MOU",
        "articles of incorporation",
        "bylaws",
        "power of attorney",
    ],
    "courts": [
        "Supreme Court",
        "Circuit Court",
        "District Court",
        "Bankruptcy Court",
        "Tax Court",
        "Family Court",
        "Probate Court",
        "Small Claims",
    ],
    "jurisdictions": ["federal", "state", "local", "international", "tribal", "maritime", "bankruptcy", "tax"],
}

EDUCATION_TEMPLATES = {
    "degrees": ["Bachelor", "Master", "PhD", "Associate", "MBA", "JD", "MD", "EdD", "Certificate", "Diploma"],
    "fields": [
        "Computer Science",
        "Data Science",
        "Business",
        "Engineering",
        "Psychology",
        "Biology",
        "Economics",
        "Education",
        "Nursing",
        "Law",
    ],
    "institutions": [
        "university",
        "college",
        "community college",
        "trade school",
        "bootcamp",
        "online platform",
        "MOOC",
        "professional certification",
    ],
    "pedagogy": [
        "lecture",
        "seminar",
        "lab",
        "project-based",
        "flipped classroom",
        "peer instruction",
        "active learning",
        "experiential learning",
    ],
    "accreditation": [
        "regional accreditation",
        "national accreditation",
        "programmatic accreditation",
        "ABET",
        "AACSB",
        "CCNE",
        "CAEP",
    ],
}

SECURITY_TEMPLATES = {
    "vulnerabilities": [
        "SQL injection",
        "XSS",
        "CSRF",
        "RCE",
        "LFI",
        "RFI",
        "XXE",
        "SSRF",
        "IDOR",
        "path traversal",
        "buffer overflow",
        "use after free",
    ],
    "tools": [
        "Burp Suite",
        "OWASP ZAP",
        "Nmap",
        "Metasploit",
        "sqlmap",
        "Nikto",
        "Dirb",
        "Gobuster",
        "Hashcat",
        "John the Ripper",
        "Wireshark",
    ],
    "concepts": [
        "authentication",
        "authorization",
        "encryption",
        "hashing",
        "salting",
        "OAuth",
        "OIDC",
        "SAML",
        "JWT",
        "MFA",
        "2FA",
        "RBAC",
        "ABAC",
        "zero trust",
    ],
    "standards": [
        "OWASP Top 10",
        "NIST CSF",
        "ISO 27001",
        "SOC 2",
        "PCI DSS",
        "HIPAA",
        "GDPR",
        "CIS Controls",
        "MITRE ATT&CK",
    ],
    "attacks": [
        "phishing",
        "spear phishing",
        "whaling",
        "ransomware",
        "DDoS",
        "MITM",
        "credential stuffing",
        "password spray",
        "brute force",
        "session hijacking",
    ],
}


# ============================================================
# GENERATION FUNCTIONS
# ============================================================


def _generate_abbreviation_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate abbreviation vs full form pairs."""
    pairs = []
    abbreviations = {
        "AI": "Artificial Intelligence",
        "ML": "Machine Learning",
        "NLP": "Natural Language Processing",
        "DL": "Deep Learning",
        "CV": "Computer Vision",
        "LLM": "Large Language Model",
        "RAG": "Retrieval Augmented Generation",
        "CNN": "Convolutional Neural Network",
        "RNN": "Recurrent Neural Network",
        "LSTM": "Long Short-Term Memory",
        "GPU": "Graphics Processing Unit",
        "TPU": "Tensor Processing Unit",
        "API": "Application Programming Interface",
        "SDK": "Software Development Kit",
        "IDE": "Integrated Development Environment",
        "CI": "Continuous Integration",
        "CD": "Continuous Deployment",
        "DB": "Database",
        "ORM": "Object Relational Mapping",
        "SQL": "Structured Query Language",
        "NoSQL": "Not Only SQL",
        "REST": "Representational State Transfer",
        "GraphQL": "Graph Query Language",
        "gRPC": "Google Remote Procedure Call",
        "DNS": "Domain Name System",
        "DHCP": "Dynamic Host Configuration Protocol",
        "VPN": "Virtual Private Network",
        "SSH": "Secure Shell",
        "TLS": "Transport Layer Security",
        "SSL": "Secure Sockets Layer",
        "HTTP": "HyperText Transfer Protocol",
        "JSON": "JavaScript Object Notation",
        "XML": "Extensible Markup Language",
        "YAML": "YAML Ain't Markup Language",
        "HTML": "HyperText Markup Language",
        "CSS": "Cascading Style Sheets",
        "JS": "JavaScript",
        "TS": "TypeScript",
        "CPU": "Central Processing Unit",
        "RAM": "Random Access Memory",
        "SSD": "Solid State Drive",
        "HDD": "Hard Disk Drive",
        "USB": "Universal Serial Bus",
        "OS": "Operating System",
        "VM": "Virtual Machine",
        "K8s": "Kubernetes",
        "TF": "TensorFlow",
        "PT": "PyTorch",
    }

    for abbr, full in random.sample(list(abbreviations.items()), min(count, len(abbreviations))):
        # Non-duplicate: abbreviation vs full form in different contexts
        templates_cat = templates.get(category.value, {})
        if templates_cat:
            context = random.choice(list(templates_cat.values()))
            if context:
                ctx = random.choice(context)
                pairs.append(
                    HardPair(
                        q1=f"What is {abbr} in {ctx}?",
                        q2=f"Explain {full} for {ctx}",
                        true_label=0,  # Different questions about same concept
                        category=category,
                        difficulty_types=[DifficultyType.ABBREVIATION],
                        description=f"Abbreviation '{abbr}' vs full form '{full}' in {ctx} context",
                        expected_fp_reason="Models may match abbreviation to full form",
                    )
                )

    return pairs


def _generate_synonym_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate synonym pairs (non-duplicate)."""
    pairs = []
    synonyms = [
        ("learn", "study"),
        ("teach", "educate"),
        ("install", "setup"),
        ("configure", "set up"),
        ("remove", "delete"),
        ("uninstall", "remove"),
        ("disable", "turn off"),
        ("enable", "turn on"),
        ("start", "begin"),
        ("stop", "halt"),
        ("fix", "resolve"),
        ("debug", "troubleshoot"),
        ("create", "build"),
        ("make", "construct"),
        ("run", "execute"),
        ("deploy", "release"),
        ("test", "verify"),
        ("check", "validate"),
        ("optimize", "improve"),
        ("scale", "grow"),
        ("monitor", "observe"),
        ("log", "record"),
        ("backup", "archive"),
        ("restore", "recover"),
        ("migrate", "move"),
        ("upgrade", "update"),
        ("downgrade", "revert"),
        ("refactor", "rewrite"),
    ]

    for w1, w2 in random.sample(synonyms, min(count, len(synonyms))):
        templates_cat = templates.get(category.value, {})
        if templates_cat:
            context = random.choice(list(templates_cat.values()))
            if context:
                ctx = random.choice(context)
                pairs.append(
                    HardPair(
                        q1=f"How to {w1} {ctx}?",
                        q2=f"Guide to {w2} {ctx}",
                        true_label=0,
                        category=category,
                        difficulty_types=[DifficultyType.SYNONYM],
                        description=f"Synonyms '{w1}' vs '{w2}' in {ctx} context",
                        expected_fp_reason="Models may treat synonyms as duplicate intent",
                    )
                )

    return pairs


def _generate_negation_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate negation pairs (non-duplicate)."""
    pairs = []
    negation_pairs = [
        ("install", "uninstall"),
        ("enable", "disable"),
        ("start", "stop"),
        ("create", "delete"),
        ("add", "remove"),
        ("allow", "deny"),
        ("connect", "disconnect"),
        ("mount", "unmount"),
        ("load", "unload"),
        ("activate", "deactivate"),
        ("grant", "revoke"),
        ("include", "exclude"),
        ("accept", "reject"),
        ("approve", "deny"),
        ("encrypt", "decrypt"),
        ("compress", "decompress"),
        ("lock", "unlock"),
        ("sign", "verify"),
        ("encode", "decode"),
        ("push", "pull"),
        ("upload", "download"),
    ]

    for pos, neg in random.sample(negation_pairs, min(count, len(negation_pairs))):
        templates_cat = templates.get(category.value, {})
        if templates_cat:
            context = random.choice(list(templates_cat.values()))
            if context:
                ctx = random.choice(context)
                pairs.append(
                    HardPair(
                        q1=f"Can I {pos} {ctx}?",
                        q2=f"How to {neg} {ctx}?",
                        true_label=0,
                        category=category,
                        difficulty_types=[DifficultyType.NEGATION, DifficultyType.CONTRADICTION],
                        description=f"Opposite actions: {pos} vs {neg} for {ctx}",
                        expected_fp_reason="High lexical overlap with opposite intent",
                    )
                )

    return pairs


def _generate_paraphrase_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate paraphrase pairs (these ARE duplicates)."""
    pairs = []
    paraphrases = [
        ("How to {action} {target}?", "Guide for {action} {target}"),
        ("What is the best way to {action} {target}?", "How do I {action} {target}?"),
        ("Steps to {action} {target}", "Tutorial: {action} {target}"),
        ("Can I {action} {target}?", "Is it possible to {action} {target}?"),
        ("Explain how to {action} {target}", "Show me how to {action} {target}"),
        ("Method for {action} {target}", "Procedure to {action} {target}"),
        ("How do you {action} {target}?", "What's the process to {action} {target}?"),
    ]

    templates_cat = templates.get(category.value, {})
    if not templates_cat:
        return pairs

    for template in random.sample(paraphrases, min(count, len(paraphrases))):
        context = random.choice(list(templates_cat.values()))
        if context:
            target = random.choice(context)
            action = random.choice(["install", "configure", "setup", "use", "debug", "test", "deploy"])
            q1 = template[0].format(action=action, target=target)
            q2 = template[1].format(action=action, target=target)
            pairs.append(
                HardPair(
                    q1=q1,
                    q2=q2,
                    true_label=1,
                    category=category,
                    difficulty_types=[DifficultyType.PARAPHRASE],
                    description=f"Paraphrase pair for {action} {target}",
                    expected_fp_reason="Should be correctly identified as duplicate",
                )
            )

    return pairs


def _generate_entity_swap_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate entity swap pairs (non-duplicate)."""
    pairs = []
    templates_cat = templates.get(category.value, {})

    entity_pairs = []
    for entity_type, entities in templates_cat.items():
        if len(entities) >= 2:
            for e1, e2 in zip(entities[: len(entities) // 2], entities[len(entities) // 2 :], strict=False):
                entity_pairs.append((entity_type, e1, e2))

    for entity_type, e1, e2 in random.sample(entity_pairs, min(count, len(entity_pairs))):
        action = random.choice(["install", "use", "configure", "debug", "compare", "learn"])
        pairs.append(
            HardPair(
                q1=f"How to {action} {e1}?",
                q2=f"What is {e2} used for?",
                true_label=0,
                category=category,
                difficulty_types=[DifficultyType.ENTITY_SWAP],
                description=f"Different {entity_type}: {e1} vs {e2}",
                expected_fp_reason="Models may confuse similar entity types",
            )
        )

    return pairs


def _generate_contradiction_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate contradiction pairs (non-duplicate)."""
    pairs = []
    contradiction_pairs = [
        ("before", "after"),
        ("pre", "post"),
        ("enable", "disable"),
        ("allow", "block"),
        ("grant", "deny"),
        ("require", "optional"),
        ("mandatory", "optional"),
        ("sync", "async"),
        ("blocking", "non-blocking"),
        ("compile-time", "runtime"),
        ("static", "dynamic"),
        ("strong", "weak"),
        ("client", "server"),
        ("frontend", "backend"),
        ("producer", "consumer"),
        ("publisher", "subscriber"),
        ("leader", "follower"),
        ("primary", "replica"),
        ("read", "write"),
        ("input", "output"),
        ("request", "response"),
        ("free", "paid"),
        ("open source", "proprietary"),
        ("cloud", "on-premise"),
    ]

    for w1, w2 in random.sample(contradiction_pairs, min(count, len(contradiction_pairs))):
        templates_cat = templates.get(category.value, {})
        if templates_cat:
            context = random.choice(list(templates_cat.values()))
            if context:
                ctx = random.choice(context)
                pairs.append(
                    HardPair(
                        q1=f"Should I do {w1} {ctx} or {w2} {ctx}?",
                        q2=f"Is it better to {w1} {ctx} than {w2} {ctx}?",
                        true_label=0,
                        category=category,
                        difficulty_types=[DifficultyType.CONTRADICTION],
                        description=f"Contradictory concepts: {w1} vs {w2} for {ctx}",
                        expected_fp_reason="Models may match on shared context, miss contradiction",
                    )
                )

    return pairs


def _generate_version_mismatch_pairs(category: Category, templates: dict, count: int) -> list[HardPair]:
    """Generate version mismatch pairs (non-duplicate)."""
    pairs = []
    version_pairs = [
        ("Python 2", "Python 3"),
        ("Python 3.8", "Python 3.11"),
        ("Java 8", "Java 17"),
        ("Node 14", "Node 20"),
        ("React 16", "React 18"),
        ("AngularJS", "Angular 17"),
        ("Spring 4", "Spring 6"),
        ("Django 2", "Django 4"),
        ("TensorFlow 1", "TensorFlow 2"),
        ("PyTorch 1.x", "PyTorch 2.x"),
        ("Kubernetes 1.20", "Kubernetes 1.28"),
        ("Ubuntu 18.04", "Ubuntu 22.04"),
        ("CentOS 7", "CentOS Stream 9"),
        ("Windows 10", "Windows 11"),
        ("macOS Monterey", "macOS Ventura"),
        ("MySQL 5.7", "MySQL 8.0"),
        ("PostgreSQL 12", "PostgreSQL 15"),
    ]

    for v1, v2 in random.sample(version_pairs, min(count, len(version_pairs))):
        templates_cat = templates.get(category.value, {})
        if templates_cat:
            context = random.choice(list(templates_cat.values()))
            if context:
                ctx = random.choice(context)
                pairs.append(
                    HardPair(
                        q1=f"How to {ctx} in {v1}?",
                        q2=f"Does {ctx} work the same in {v2}?",
                        true_label=0,
                        category=category,
                        difficulty_types=[DifficultyType.VERSION_MISMATCH],
                        description=f"Version mismatch: {v1} vs {v2} for {ctx}",
                        expected_fp_reason="Models may not distinguish version-specific differences",
                    )
                )

    return pairs


# ============================================================
# MAIN GENERATION FUNCTION
# ============================================================

ALL_TEMPLATES = {
    Category.PROGRAMMING: PROGRAMMING_TEMPLATES,
    Category.LINUX: LINUX_TEMPLATES,
    Category.AI_ML: AI_ML_TEMPLATES,
    Category.CLOUD: CLOUD_TEMPLATES,
    Category.NETWORKING: NETWORKING_TEMPLATES,
    Category.MEDICINE: MEDICINE_TEMPLATES,
    Category.FINANCE: FINANCE_TEMPLATES,
    Category.MATH: MATH_TEMPLATES,
    Category.GENERAL: GENERAL_TEMPLATES,
    Category.LEGAL: LEGAL_TEMPLATES,
    Category.EDUCATION: EDUCATION_TEMPLATES,
    Category.SECURITY: SECURITY_TEMPLATES,
}

GENERATORS = [
    _generate_abbreviation_pairs,
    _generate_synonym_pairs,
    _generate_negation_pairs,
    _generate_paraphrase_pairs,
    _generate_entity_swap_pairs,
    _generate_contradiction_pairs,
    _generate_version_mismatch_pairs,
]


def generate_hard_dataset(
    total_pairs: int = 1000,
    categories: list[Category] | None = None,
    difficulty_types: list[DifficultyType] | None = None,
    seed: int = 42,
) -> list[HardPair]:
    """Generate hard test dataset.

    Args:
        total_pairs: Total number of pairs to generate
        categories: Specific categories to include (None = all)
        difficulty_types: Specific difficulty types to include (None = all)
        seed: Random seed for reproducibility

    Returns:
        List of HardPair objects
    """
    random.seed(seed)

    if categories is None:
        categories = list(Category)

    all_pairs = []
    pairs_per_category = total_pairs // len(categories)
    remaining = total_pairs % len(categories)

    for i, category in enumerate(categories):
        cat_count = pairs_per_category + (1 if i < remaining else 0)
        templates = ALL_TEMPLATES.get(category, {})

        cat_pairs = []
        # Distribute across generators
        per_generator = max(1, cat_count // len(GENERATORS))

        for generator in GENERATORS:
            try:
                generated = generator(category, templates, per_generator)
                cat_pairs.extend(generated)
            except Exception:
                continue

        # Also add some paraphrases (duplicates) for balance
        paraphrases = _generate_paraphrase_pairs(category, templates, per_generator)
        cat_pairs.extend(paraphrases)

        # Truncate to desired count
        random.shuffle(cat_pairs)
        all_pairs.extend(cat_pairs[:cat_count])

    # Shuffle final list
    random.shuffle(all_pairs)

    # Filter by difficulty types if specified
    if difficulty_types:
        all_pairs = [p for p in all_pairs if any(dt in p.difficulty_types for dt in difficulty_types)]

    return all_pairs[:total_pairs]


def save_dataset(pairs: list[HardPair], path: Path) -> None:
    """Save dataset to CSV and JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # CSV
    df = pd.DataFrame(
        [
            {
                "q1": p.q1,
                "q2": p.q2,
                "true_label": p.true_label,
                "category": p.category.value,
                "difficulty_types": ";".join(dt.value for dt in p.difficulty_types),
                "description": p.description,
                "expected_fp_reason": p.expected_fp_reason,
            }
            for p in pairs
        ]
    )

    csv_path = path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)

    # JSON
    json_path = path.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(
            [
                {
                    "q1": p.q1,
                    "q2": p.q2,
                    "true_label": p.true_label,
                    "category": p.category.value,
                    "difficulty_types": [dt.value for dt in p.difficulty_types],
                    "description": p.description,
                    "expected_fp_reason": p.expected_fp_reason,
                }
                for p in pairs
            ],
            f,
            indent=2,
        )

    # Stats
    stats_path = path.with_suffix(".stats.json")
    stats = {
        "total_pairs": len(pairs),
        "duplicates": sum(1 for p in pairs if p.true_label == 1),
        "non_duplicates": sum(1 for p in pairs if p.true_label == 0),
        "by_category": {},
        "by_difficulty": {},
    }

    for p in pairs:
        cat = p.category.value
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        for dt in p.difficulty_types:
            stats["by_difficulty"][dt.value] = stats["by_difficulty"].get(dt.value, 0) + 1

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)


def load_dataset(path: Path) -> list[HardPair]:
    """Load dataset from JSON."""
    path = Path(path)
    with open(path) as f:
        data = json.load(f)

    pairs = []
    for item in data:
        pairs.append(
            HardPair(
                q1=item["q1"],
                q2=item["q2"],
                true_label=item["true_label"],
                category=Category(item["category"]),
                difficulty_types=[DifficultyType(dt) for dt in item["difficulty_types"]],
                description=item["description"],
                expected_fp_reason=item.get("expected_fp_reason", ""),
            )
        )

    return pairs


def print_dataset_stats(pairs: list[HardPair]) -> None:
    """Print dataset statistics."""
    _logger.info("=" * 60)
    _logger.info("Hard Test Dataset Statistics")
    _logger.info("=" * 60)
    _logger.info("Total pairs: %s", len(pairs))
    _logger.info("  Duplicates: %s", sum(1 for p in pairs if p.true_label == 1))
    _logger.info("  Non-duplicates: %s", sum(1 for p in pairs if p.true_label == 0))

    _logger.info("By Category:")
    cat_counts = {}
    for p in pairs:
        cat_counts[p.category.value] = cat_counts.get(p.category.value, 0) + 1
    for cat, count in sorted(cat_counts.items()):
        _logger.info("  %s: %s", cat, count)

    _logger.info("By Difficulty Type:")
    diff_counts = {}
    for p in pairs:
        for dt in p.difficulty_types:
            diff_counts[dt.value] = diff_counts.get(dt.value, 0) + 1
    for dt, count in sorted(diff_counts.items()):
        _logger.info("  %s: %s", dt, count)

    _logger.info("Sample Pairs:")
    for i, p in enumerate(pairs[:5]):
        label = "Duplicate" if p.true_label == 1 else "Non-Duplicate"
        _logger.info("  %s. [%s] %s", i + 1, label, p.q1)
        _logger.info("     %s", p.q2)
        _logger.info("     Category: %s, Types: %s", p.category.value, [dt.value for dt in p.difficulty_types])


if __name__ == "__main__":
    # Generate and save dataset
    pairs = generate_hard_dataset(1000, seed=42)
    print_dataset_stats(pairs)
    save_dataset(pairs, Path("hard_test_dataset"))
    _logger.info("Dataset saved to hard_test_dataset.csv/.json")
