from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ares._config import AppPaths, get_app_paths, get_config


class ModelTier(Enum):
    PRODUCTION = "production"
    RESEARCH = "research"
    LEGACY = "legacy"
    EXPERIMENTAL = "experimental"


class ModelHealth(Enum):
    READY = "ready"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    DOWNLOADING = "downloading"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"


class ModelBackend(Enum):
    CLASSICAL_ML = "classical-ml"
    TRANSFORMER = "transformer"
    BI_ENCODER = "bi-encoder"
    CROSS_ENCODER = "cross-encoder"
    ENSEMBLE = "ensemble"
    EMBEDDING = "embedding"


class ModelFamily(Enum):
    TFIDF = "tfidf"
    DISTILBERT = "distilbert"
    BGE = "bge"
    E5 = "e5"
    MPNET = "mpnet"
    DEBERTA = "deberta"
    CROSS_ENCODER_QUORA = "cross-encoder-quora"
    ENSEMBLE = "ensemble"


@dataclass
class ModelCapabilities:
    supports_batch: bool = False
    supports_stream: bool = False
    supports_embedding: bool = False
    supports_cross_encoding: bool = False
    supports_calibration: bool = False
    supports_explainability: bool = False
    supports_gpu: bool = False
    supports_quantization: bool = False


@dataclass
class ModelEntry:
    id: str = ""
    display_name: str = ""
    internal_id: str = ""
    backend: ModelBackend = ModelBackend.TRANSFORMER
    family: ModelFamily = ModelFamily.DISTILBERT
    architecture: str = ""
    task: str = "duplicate-detection"
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    artifact_path: str | None = None
    hub_name: str | None = None
    device: str = "cpu"
    status: ModelHealth = ModelHealth.MISSING
    availability: str = "unknown"
    parameter_count: str = "N/A"
    memory_usage_mb: float | None = None
    embedding_size: int | None = None
    hidden_size: int | None = None
    framework: str = ""
    source: str = ""
    version: str = ""
    is_loaded: bool = False
    has_artifacts: bool = False
    load_error: str | None = None
    description: str = ""
    advantages: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommended_use: str = ""
    model_tier: str = "research"

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())


def _get_directory_size_mb(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024) if total else None


def _get_hf_cache_path(model_key: str) -> str | None:
    try:
        from huggingface_hub import scan_cache_dir
        from huggingface_hub.errors import CacheNotFound

        cache = scan_cache_dir()
        for repo in cache.repos:
            if model_key.replace("/", "--") in str(repo.repo_id) or model_key in str(repo.repo_id):
                return str(repo.repo_path)
    except (OSError, ImportError, CacheNotFound):
        pass
    home = Path.home()
    paths_cfg = get_config("paths") or {}
    candidates = [
        paths_cfg.get("hf_cache_dir") or str(home / ".cache" / "huggingface" / "hub"),
        paths_cfg.get("st_cache_dir") or str(home / ".cache" / "torch" / "sentence_transformers"),
    ]
    for cache_dir in candidates:
        cp = Path(cache_dir)
        if cp.exists():
            for sub in cp.rglob("*"):
                if model_key.replace("/", "_") in sub.name or model_key.replace("/", "--") in sub.name:
                    return str(sub)
    return None


def _check_artifacts(path: Path) -> bool:
    if not path.exists():
        return False
    has_config = (path / "config.json").exists()
    has_weights = (
        (path / "model.safetensors").exists()
        or (path / "pytorch_model.bin").exists()
        or any(f.suffix == ".joblib" for f in path.iterdir())
    )
    return has_config and has_weights


def _get_hub_name(model_key: str) -> str | None:
    cfg = get_config("models") or {}
    hub_names = cfg.get("hub_names", {})
    return hub_names.get(model_key)


_registry_cache: list[ModelEntry] | None = None
_registry_cache_key: str | None = None


def _registry_cache_key_from_paths(paths: AppPaths | None) -> str:
    if paths is None:
        paths = get_app_paths()
    return hashlib.md5(str(paths.models_dir).encode()).hexdigest()


def build_registry(paths: AppPaths | None = None) -> list[ModelEntry]:
    if paths is None:
        paths = get_app_paths()

    hub_names = (get_config("models") or {}).get("hub_names", {})

    week2_tfidf_path = paths.models_dir / "week2_models" / "logistic_regression.joblib"
    week2_svm_path = paths.models_dir / "week2_models" / "linear_svm.joblib"
    week2_dir_size = _get_directory_size_mb(paths.models_dir / "week2_models")
    week2_available = week2_tfidf_path.exists() and week2_svm_path.exists()

    bge_cached = _get_hf_cache_path("BAAI/bge-base-en-v1.5") is not None
    e5_cached = _get_hf_cache_path("intfloat/e5-base-v2") is not None
    mpnet_cached = _get_hf_cache_path("sentence-transformers/all-mpnet-base-v2") is not None
    deberta_cached = _get_hf_cache_path("cross-encoder/nli-deberta-v3-base") is not None

    global _registry_cache, _registry_cache_key
    cache_key = _registry_cache_key_from_paths(paths)
    if _registry_cache is not None and _registry_cache_key == cache_key:
        return list(_registry_cache)

    entries: list[ModelEntry] = []

    entries.append(
        ModelEntry(
            display_name="TF-IDF + Logistic Regression (Week 2)",
            internal_id="week2_lr",
            model_tier="legacy",
            backend=ModelBackend.CLASSICAL_ML,
            family=ModelFamily.TFIDF,
            architecture="LogisticRegression",
            artifact_path=str(week2_tfidf_path) if week2_tfidf_path.exists() else None,
            device="cpu",
            status=ModelHealth.READY if week2_available else ModelHealth.MISSING,
            availability="local" if week2_available else "missing",
            parameter_count="~5K features (TF-IDF)",
            memory_usage_mb=week2_dir_size,
            framework="joblib",
            source="local",
            version="week2",
            has_artifacts=week2_available,
            capabilities=ModelCapabilities(supports_batch=True, supports_calibration=False, supports_gpu=False),
            description="Logistic Regression with TF-IDF n-gram features (1,2). Classical baseline.",
            advantages=["Fast inference", "Interpretable", "Works well with high lexical overlap"],
            weaknesses=["No semantic understanding", "Fails on abbreviation/synonym pairs"],
            recommended_use="Quick baselines, pairs with high word overlap",
        )
    )

    entries.append(
        ModelEntry(
            display_name="TF-IDF + Linear SVM (Week 2)",
            internal_id="week2_svm",
            model_tier="legacy",
            backend=ModelBackend.CLASSICAL_ML,
            family=ModelFamily.TFIDF,
            architecture="LinearSVM",
            artifact_path=str(week2_svm_path) if week2_svm_path.exists() else None,
            device="cpu",
            status=ModelHealth.READY if week2_available else ModelHealth.MISSING,
            availability="local" if week2_available else "missing",
            parameter_count="~5K features (TF-IDF)",
            memory_usage_mb=week2_dir_size,
            framework="joblib",
            source="local",
            version="week2",
            has_artifacts=week2_available,
            capabilities=ModelCapabilities(supports_batch=True, supports_calibration=False, supports_gpu=False),
            description="Linear SVM with TF-IDF n-gram features. Handles high-dimensional sparse data well.",
            advantages=["Good for high-dimensional data", "Max-margin separation"],
            weaknesses=["No probability calibration", "No semantic understanding"],
            recommended_use="Baseline comparison, pairs with high word overlap",
        )
    )

    w3_path = paths.week3_model_dir
    w3_ready = _check_artifacts(w3_path)
    w3_size = _get_directory_size_mb(w3_path)
    entries.append(
        ModelEntry(
            display_name="DistilBERT (Week 3)",
            internal_id="week3",
            model_tier="production",
            backend=ModelBackend.TRANSFORMER,
            family=ModelFamily.DISTILBERT,
            architecture="DistilBERTForSequenceClassification",
            artifact_path=str(w3_path) if w3_ready else None,
            device="cpu",
            status=ModelHealth.READY if w3_ready else ModelHealth.MISSING,
            availability="local" if w3_ready else "missing",
            parameter_count="66.9M",
            memory_usage_mb=w3_size,
            embedding_size=768,
            hidden_size=768,
            framework="pytorch",
            source="local",
            version="week3",
            has_artifacts=w3_ready,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_calibration=True, supports_explainability=True, supports_gpu=True
            ),
            description="Fine-tuned DistilBERT for sequence classification. Transformer baseline.",
            advantages=["Contextual understanding", "Handles paraphrasing well"],
            weaknesses=["Conservative predictions", "Slow on CPU (~500ms)"],
            recommended_use="Semantic pairs, general purpose duplicate detection",
        )
    )

    w4_path = paths.week4_model_dir
    w4_ready = _check_artifacts(w4_path)
    w4_size = _get_directory_size_mb(w4_path)
    entries.append(
        ModelEntry(
            display_name="Improved DistilBERT (Week 4)",
            internal_id="week4",
            model_tier="production",
            backend=ModelBackend.TRANSFORMER,
            family=ModelFamily.DISTILBERT,
            architecture="DistilBERTForSequenceClassification",
            artifact_path=str(w4_path) if w4_ready else None,
            device="cpu",
            status=ModelHealth.READY if w4_ready else ModelHealth.MISSING,
            availability="local" if w4_ready else "missing",
            parameter_count="66.9M",
            memory_usage_mb=w4_size,
            embedding_size=768,
            hidden_size=768,
            framework="pytorch",
            source="local",
            version="week4",
            has_artifacts=w4_ready,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_calibration=True, supports_explainability=True, supports_gpu=True
            ),
            description="Week 4 DistilBERT with tuned threshold, class weighting, and error analysis.",
            advantages=["Tuned threshold (best F1)", "Class-weighted training", "Error analysis artifacts"],
            weaknesses=["Conservative predictions", "Same architecture as Week 3"],
            recommended_use="When Week 3 is too conservative; tuned threshold needed",
        )
    )

    bge_local = paths.bge_model_dir.exists()
    bge_avail = _check_artifacts(paths.bge_model_dir) if bge_local else bge_cached
    bge_size = _get_directory_size_mb(paths.bge_model_dir) if bge_local else None
    entries.append(
        ModelEntry(
            display_name="BGE-base-en-v1.5",
            internal_id="bge",
            model_tier="research",
            backend=ModelBackend.BI_ENCODER,
            family=ModelFamily.BGE,
            architecture="SentenceTransformer",
            hub_name=hub_names.get("BGE-base-en-v1.5", "BAAI/bge-base-en-v1.5"),
            artifact_path=str(paths.bge_model_dir) if bge_local else _get_hf_cache_path("BAAI/bge-base-en-v1.5"),
            device="cpu",
            status=ModelHealth.READY if bge_avail else ModelHealth.DOWNLOADING if bge_cached else ModelHealth.MISSING,
            availability="local" if bge_local else ("cached" if bge_cached else "auto-download"),
            parameter_count="110M",
            memory_usage_mb=bge_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            has_artifacts=bge_cached or bge_local,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_embedding=True, supports_calibration=True, supports_gpu=True
            ),
            description="BGE (BAAI General Embedding) — high-quality bi-encoder for semantic similarity.",
            advantages=["Strong semantic understanding", "Good generalization", "Supports abbreviations"],
            weaknesses=["Over-predicts duplicates on similar topics", "CPU inference ~200ms"],
            recommended_use="Semantic pairs, abbreviation detection, synonym detection",
        )
    )

    e5_local = paths.e5_model_dir.exists()
    e5_avail = _check_artifacts(paths.e5_model_dir) if e5_local else e5_cached
    e5_size = _get_directory_size_mb(paths.e5_model_dir) if e5_local else None
    entries.append(
        ModelEntry(
            display_name="E5-base-v2",
            internal_id="e5",
            model_tier="experimental",
            backend=ModelBackend.BI_ENCODER,
            family=ModelFamily.E5,
            architecture="SentenceTransformer",
            hub_name=hub_names.get("E5-base-v2", "intfloat/e5-base-v2"),
            artifact_path=str(paths.e5_model_dir) if e5_local else _get_hf_cache_path("intfloat/e5-base-v2"),
            device="cpu",
            status=ModelHealth.READY if e5_avail else ModelHealth.DOWNLOADING if e5_cached else ModelHealth.MISSING,
            availability="local" if e5_local else ("cached" if e5_cached else "auto-download"),
            parameter_count="118M",
            memory_usage_mb=e5_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            has_artifacts=e5_cached or e5_local,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_embedding=True, supports_calibration=True, supports_gpu=True
            ),
            description="E5 (EmbEddings from bidirEctional Encoder rEpresentations) — contrastive learned embeddings.",
            advantages=["Contrastive pre-training", "Strong on similarity tasks"],
            weaknesses=["Requires query/passage prefix", "Highest false positive rate"],
            recommended_use="When maximum recall for semantic matches is needed",
        )
    )

    e5_ft_path = paths.finetuned_e5_dir
    e5_ft_ready = _check_artifacts(e5_ft_path)
    e5_ft_size = _get_directory_size_mb(e5_ft_path)
    entries.append(
        ModelEntry(
            display_name="E5-quora-finetuned",
            internal_id="e5_ft",
            model_tier="research",
            backend=ModelBackend.BI_ENCODER,
            family=ModelFamily.E5,
            architecture="SentenceTransformer",
            artifact_path=str(e5_ft_path) if e5_ft_ready else None,
            device="cpu",
            status=ModelHealth.READY if e5_ft_ready else ModelHealth.MISSING,
            availability="local" if e5_ft_ready else "missing",
            parameter_count="118M",
            memory_usage_mb=e5_ft_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="local",
            version="phase2",
            has_artifacts=e5_ft_ready,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_embedding=True, supports_calibration=True, supports_gpu=True
            ),
            description="E5 fine-tuned on Quora duplicate detection data.",
            advantages=["Fine-tuned for task", "Highest bi-encoder accuracy"],
            weaknesses=["Slower than base E5", "Larger model size"],
            recommended_use="Primary bi-encoder for semantic duplicate detection",
        )
    )

    mpnet_local = paths.mpnet_model_dir.exists()
    mpnet_avail = _check_artifacts(paths.mpnet_model_dir) if mpnet_local else mpnet_cached
    mpnet_size = _get_directory_size_mb(paths.mpnet_model_dir) if mpnet_local else None
    entries.append(
        ModelEntry(
            display_name="MPNet-base-v2",
            internal_id="mpnet",
            model_tier="research",
            backend=ModelBackend.BI_ENCODER,
            family=ModelFamily.MPNET,
            architecture="SentenceTransformer",
            hub_name=hub_names.get("MPNet-base-v2", "sentence-transformers/all-mpnet-base-v2"),
            artifact_path=str(paths.mpnet_model_dir)
            if mpnet_local
            else _get_hf_cache_path("sentence-transformers/all-mpnet-base-v2"),
            device="cpu",
            status=ModelHealth.READY
            if mpnet_avail
            else ModelHealth.DOWNLOADING
            if mpnet_cached
            else ModelHealth.MISSING,
            availability="local" if mpnet_local else ("cached" if mpnet_cached else "auto-download"),
            parameter_count="110M",
            memory_usage_mb=mpnet_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            has_artifacts=mpnet_cached or mpnet_local,
            capabilities=ModelCapabilities(
                supports_batch=True, supports_embedding=True, supports_calibration=True, supports_gpu=True
            ),
            description="MPNet — masked and permuted language modeling. Best overall bi-encoder for this task.",
            advantages=["Best discrimination among bi-encoders", "Robust predictions"],
            weaknesses=["Slightly slower than BGE", "Still over-predicts on similar topics"],
            recommended_use="Primary bi-encoder for semantic duplicate detection",
        )
    )

    deberta_local = paths.deberta_model_dir.exists()
    deberta_avail = _check_artifacts(paths.deberta_model_dir) if deberta_local else deberta_cached
    deberta_size = _get_directory_size_mb(paths.deberta_model_dir) if deberta_local else None
    entries.append(
        ModelEntry(
            display_name="DeBERTa-v3 Cross-Encoder",
            internal_id="deberta",
            model_tier="experimental",
            backend=ModelBackend.CROSS_ENCODER,
            family=ModelFamily.DEBERTA,
            architecture="CrossEncoder",
            hub_name=hub_names.get("DeBERTa-v3-Cross-Encoder", "cross-encoder/nli-deberta-v3-base"),
            artifact_path=str(paths.deberta_model_dir)
            if deberta_local
            else _get_hf_cache_path("cross-encoder/nli-deberta-v3-base"),
            device="cpu",
            status=ModelHealth.READY
            if deberta_avail
            else ModelHealth.DOWNLOADING
            if deberta_cached
            else ModelHealth.MISSING,
            availability="local" if deberta_local else ("cached" if deberta_cached else "auto-download"),
            parameter_count="184M",
            memory_usage_mb=deberta_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            has_artifacts=deberta_cached or deberta_local,
            capabilities=ModelCapabilities(
                supports_batch=True,
                supports_cross_encoding=True,
                supports_calibration=True,
                supports_gpu=True,
                supports_explainability=True,
            ),
            description="DeBERTa-v3 NLI cross-encoder. Uses entailment ratio for pairwise scoring.",
            advantages=["Joint encoding captures full context", "Best accuracy on test suite"],
            weaknesses=["NLI model, not trained for duplicate detection", "Slowest inference (~400ms)"],
            recommended_use="When accuracy is critical; works best in ensemble",
        )
    )

    ce_quora_path = paths.finetuned_cross_encoder_dir
    ce_quora_ready = _check_artifacts(ce_quora_path)
    ce_quora_size = _get_directory_size_mb(ce_quora_path)
    entries.append(
        ModelEntry(
            display_name="Cross-Encoder-Quora (Trained)",
            internal_id="ce_quora",
            model_tier="production",
            backend=ModelBackend.CROSS_ENCODER,
            family=ModelFamily.CROSS_ENCODER_QUORA,
            architecture="CrossEncoder",
            artifact_path=str(ce_quora_path) if ce_quora_ready else None,
            device="cpu",
            status=ModelHealth.READY if ce_quora_ready else ModelHealth.MISSING,
            availability="local" if ce_quora_ready else "missing",
            parameter_count="184M",
            memory_usage_mb=ce_quora_size,
            embedding_size=768,
            hidden_size=768,
            framework="sentence-transformers",
            source="local",
            version="phase2",
            has_artifacts=ce_quora_ready,
            capabilities=ModelCapabilities(
                supports_batch=True,
                supports_cross_encoding=True,
                supports_calibration=True,
                supports_gpu=True,
                supports_explainability=True,
            ),
            description="Cross-Encoder fine-tuned on Quora duplicate detection data. Highest single-model accuracy.",
            advantages=["Fine-tuned for task", "Joint encoding", "Best single-model accuracy"],
            weaknesses=["Slowest inference", "Cannot precompute embeddings"],
            recommended_use="Default choice for accuracy-critical predictions",
        )
    )

    entries.append(
        ModelEntry(
            display_name="Semantic Ensemble",
            internal_id="ensemble",
            model_tier="experimental",
            backend=ModelBackend.ENSEMBLE,
            family=ModelFamily.ENSEMBLE,
            architecture="WeightedEnsemble",
            device="cpu",
            status=ModelHealth.READY,
            availability="built-in",
            parameter_count="Varies (all models)",
            framework="ensemble",
            source="built-in",
            version="ensemble",
            is_loaded=True,
            has_artifacts=True,
            capabilities=ModelCapabilities(
                supports_batch=False, supports_calibration=True, supports_explainability=True, supports_gpu=True
            ),
            description="Adaptive weighted ensemble combining all models with dynamic feature-based weights.",
            advantages=["Best overall accuracy", "Handles all pair types", "Robust via trimmed mean"],
            weaknesses=["Slowest inference (loads all models)", "Depends on all sub-models"],
            recommended_use="Default choice for all predictions. Highest quality.",
        )
    )

    _registry_cache = list(entries)
    _registry_cache_key = cache_key
    return entries


def find_entry(display_name: str, paths: AppPaths | None = None) -> ModelEntry | None:
    for entry in build_registry(paths):
        if entry.display_name == display_name:
            return entry
    return None


def get_registry_dict(paths: AppPaths | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": e.id,
            "display_name": e.display_name,
            "internal_id": e.internal_id,
            "backend": e.backend.value,
            "family": e.family.value,
            "architecture": e.architecture,
            "device": e.device,
            "status": e.status.value,
            "availability": e.availability,
            "parameter_count": e.parameter_count,
            "memory_usage_mb": f"{e.memory_usage_mb:.1f}" if e.memory_usage_mb else "N/A",
            "embedding_size": e.embedding_size,
            "hidden_size": e.hidden_size,
            "framework": e.framework,
            "source": e.source,
            "version": e.version,
            "is_loaded": e.is_loaded,
            "has_artifacts": e.has_artifacts,
            "description": e.description,
            "capabilities": {
                "batch": e.capabilities.supports_batch,
                "stream": e.capabilities.supports_stream,
                "embedding": e.capabilities.supports_embedding,
                "cross_encoding": e.capabilities.supports_cross_encoding,
                "calibration": e.capabilities.supports_calibration,
                "explainability": e.capabilities.supports_explainability,
                "gpu": e.capabilities.supports_gpu,
            },
            "advantages": e.advantages,
            "weaknesses": e.weaknesses,
            "recommended_use": e.recommended_use,
        }
        for e in build_registry(paths)
    ]


def list_models() -> list[str]:
    return [e.display_name for e in build_registry()]


def get_backend_for_model(model_name: str) -> str:
    entry = find_entry(model_name)
    if entry is None:
        return "unknown"
    return entry.backend.value
