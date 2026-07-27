from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from duplicate_question_app._config.settings import AppPaths, get_app_paths, get_config
from duplicate_question_app._models.week2 import check_week2_artifacts


class ModelTier(Enum):
    PRODUCTION = "production"
    RESEARCH = "research"
    LEGACY = "legacy"
    EXPERIMENTAL = "experimental"


class ModelHealthStatus(Enum):
    READY = "ready"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    DOWNLOADING = "downloading"
    DISABLED = "disabled"
    UNSUPPORTED = "unsupported"


@dataclass
class ModelRegistryEntry:
    uid: str = ""
    display_name: str = ""
    internal_id: str = ""
    model_type: str = ""
    framework: str = ""
    source: str = ""
    version: str = ""
    local_path: str | None = None
    cache_path: str | None = None
    device: str = "cpu"
    size_mb: float | None = None
    load_status: str = "missing"
    is_loaded: bool = False
    has_artifacts: bool = False
    parameters: str = "N/A"
    embedding_size: int | None = None
    hidden_size: int | None = None
    avg_latency_ms: float = 0.0
    description: str = ""
    advantages: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommended_use: str = ""
    accuracy: float | None = None
    f1_score: float | None = None
    precision: float | None = None
    recall: float | None = None
    model_tier: str = "research"
    health_status: ModelHealthStatus = ModelHealthStatus.MISSING
    health_reason: str = ""

    def __post_init__(self) -> None:
        if not self.uid:
            self.uid = str(uuid.uuid4())


def _map_health(status_str: str, has_artifacts: bool, is_loaded: bool) -> tuple[ModelHealthStatus, str]:
    mapping = {
        "available": ModelHealthStatus.READY,
        "loaded": ModelHealthStatus.READY,
        "missing": ModelHealthStatus.MISSING,
        "downloading": ModelHealthStatus.DOWNLOADING,
    }
    status = mapping.get(status_str, ModelHealthStatus.MISSING)
    if status == ModelHealthStatus.MISSING and has_artifacts:
        status = ModelHealthStatus.CORRUPTED
    if status == ModelHealthStatus.READY and not has_artifacts:
        status = ModelHealthStatus.CORRUPTED
        return status, "artifacts missing or incomplete"
    reasons = {
        "missing": "model artifacts not found on disk or cache",
        "corrupted": "artifacts exist but are incomplete or corrupted",
        "downloading": "model will be auto-downloaded on first use",
    }
    return status, reasons.get(status.value, "")


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
    default_candidates = [
        paths_cfg.get("hf_cache_dir") or str(home / ".cache" / "huggingface" / "hub"),
        paths_cfg.get("st_cache_dir") or str(home / ".cache" / "torch" / "sentence_transformers"),
    ]
    candidates = [Path(p) for p in default_candidates]
    for cache_dir in candidates:
        if cache_dir.exists():
            for sub in cache_dir.rglob("*"):
                if model_key.replace("/", "_") in sub.name or model_key.replace("/", "--") in sub.name:
                    return str(sub)
    return None


def build_registry(paths: AppPaths | None = None) -> list[ModelRegistryEntry]:
    if paths is None:
        from pathlib import Path

        paths = get_app_paths(Path(__file__).resolve().parents[3])

    week2_arts = check_week2_artifacts(paths)
    week2_ready = all(week2_arts.values())
    resolution = None
    try:
        from duplicate_question_app._config.settings import resolve_model_selection

        resolution = resolve_model_selection(paths)
    except (FileNotFoundError, RuntimeError):
        pass

    bge_cached = _get_hf_cache_path("BAAI/bge-base-en-v1.5") is not None
    e5_cached = _get_hf_cache_path("intfloat/e5-base-v2") is not None
    mpnet_cached = _get_hf_cache_path("sentence-transformers/all-mpnet-base-v2") is not None
    deberta_cached = _get_hf_cache_path("cross-encoder/nli-deberta-v3-base") is not None

    ce_quora_on_disk = paths.finetuned_cross_encoder_dir.exists() and (
        (paths.finetuned_cross_encoder_dir / "model.safetensors").exists()
        or (paths.finetuned_cross_encoder_dir / "pytorch_model.bin").exists()
    )
    e5_ft_on_disk = paths.finetuned_e5_dir.exists() and (
        (paths.finetuned_e5_dir / "model.safetensors").exists()
        or (paths.finetuned_e5_dir / "pytorch_model.bin").exists()
    )

    entries: list[ModelRegistryEntry] = []

    # Week 2 - Logistic Regression
    lr_path = paths.models_dir / "week2_models" / "logistic_regression.joblib"
    svm_path = paths.models_dir / "week2_models" / "linear_svm.joblib"
    week2_dir_size = _get_directory_size_mb(paths.models_dir / "week2_models")

    entries.append(
        ModelRegistryEntry(
            display_name="TF-IDF + Logistic Regression (Week 2)",
            internal_id="week2_lr",
            model_tier="legacy",
            model_type="classical-ml",
            framework="joblib",
            source="local",
            version="week2",
            local_path=str(lr_path) if lr_path.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=week2_dir_size,
            load_status="available" if week2_ready else "missing",
            is_loaded=False,
            has_artifacts=week2_arts["logistic_regression"],
            parameters="~5K features (TF-IDF)",
            description="Logistic Regression with TF-IDF n-gram features (1,2). Classical baseline.",
            advantages=["Fast inference", "Interpretable", "Works well with high lexical overlap"],
            weaknesses=["No semantic understanding", "Fails on abbreviation/synonym pairs"],
            recommended_use="Quick baselines, pairs with high word overlap",
        )
    )

    # Week 2 - Linear SVM
    entries.append(
        ModelRegistryEntry(
            display_name="TF-IDF + Linear SVM (Week 2)",
            internal_id="week2_svm",
            model_tier="legacy",
            model_type="classical-ml",
            framework="joblib",
            source="local",
            version="week2",
            local_path=str(svm_path) if svm_path.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=week2_dir_size,
            load_status="available" if week2_ready else "missing",
            is_loaded=False,
            has_artifacts=week2_arts["linear_svm"],
            parameters="~5K features (TF-IDF)",
            description="Linear SVM with TF-IDF n-gram features. Handles high-dimensional sparse data well.",
            advantages=["Good for high-dimensional data", "Max-margin separation"],
            weaknesses=["No probability calibration", "No semantic understanding"],
            recommended_use="Baseline comparison, pairs with high word overlap",
        )
    )

    # Week 3 - DistilBERT
    w3_ready = resolution and resolution.week3.ready
    w3_size = _get_directory_size_mb(paths.week3_model_dir) if resolution else None
    entries.append(
        ModelRegistryEntry(
            display_name="DistilBERT (Week 3)",
            internal_id="week3",
            model_tier="production",
            model_type="transformer",
            framework="pytorch",
            source="local",
            version="week3",
            local_path=str(paths.week3_model_dir) if resolution and paths.week3_model_dir.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=w3_size,
            load_status="loaded" if w3_ready else "missing",
            is_loaded=w3_ready or False,
            has_artifacts=w3_ready or False,
            parameters="66.9M",
            embedding_size=768,
            hidden_size=768,
            description="Fine-tuned DistilBERT for sequence classification. Transformer baseline.",
            advantages=["Contextual understanding", "Handles paraphrasing well"],
            weaknesses=["Conservative predictions", "Slow on CPU (~500ms)"],
            recommended_use="Semantic pairs, general purpose duplicate detection",
        )
    )

    # Week 4 - Improved DistilBERT
    w4_ready = resolution and resolution.week4.ready
    w4_size = _get_directory_size_mb(paths.week4_model_dir) if resolution else None
    entries.append(
        ModelRegistryEntry(
            display_name="Improved DistilBERT (Week 4)",
            internal_id="week4",
            model_tier="production",
            model_type="transformer",
            framework="pytorch",
            source="local",
            version="week4",
            local_path=str(paths.week4_model_dir) if resolution and paths.week4_model_dir.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=w4_size,
            load_status="loaded" if w4_ready else "missing",
            is_loaded=w4_ready or False,
            has_artifacts=w4_ready or False,
            parameters="66.9M",
            embedding_size=768,
            hidden_size=768,
            description="Week 4 DistilBERT with tuned threshold, class weighting, and error analysis.",
            advantages=["Tuned threshold (best F1)", "Class-weighted training", "Error analysis artifacts"],
            weaknesses=["Conservative predictions", "Same architecture as Week 3"],
            recommended_use="When Week 3 is too conservative; tuned threshold needed",
        )
    )

    # BGE-base-en-v1.5
    bge_on_disk = paths.bge_model_dir.exists()
    entries.append(
        ModelRegistryEntry(
            display_name="BGE-base-en-v1.5",
            internal_id="bge",
            model_tier="research",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.bge_model_dir) if bge_on_disk else None,
            cache_path=_get_hf_cache_path("BAAI/bge-base-en-v1.5"),
            device="cpu",
            size_mb=_get_directory_size_mb(paths.bge_model_dir) if bge_on_disk else None,
            load_status="available" if (bge_cached or bge_on_disk) else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=bge_cached or bge_on_disk,
            parameters="110M",
            embedding_size=768,
            hidden_size=768,
            description="BGE (BAAI General Embedding) — high-quality bi-encoder for semantic similarity.",
            advantages=["Strong semantic understanding", "Good generalization", "Supports abbreviations"],
            weaknesses=["Over-predicts duplicates on similar topics", "CPU inference ~200ms"],
            recommended_use="Semantic pairs, abbreviation detection, synonym detection",
        )
    )

    # E5-base-v2
    e5_on_disk = paths.e5_model_dir.exists()
    entries.append(
        ModelRegistryEntry(
            display_name="E5-base-v2",
            internal_id="e5",
            model_tier="experimental",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.e5_model_dir) if e5_on_disk else None,
            cache_path=_get_hf_cache_path("intfloat/e5-base-v2"),
            device="cpu",
            size_mb=_get_directory_size_mb(paths.e5_model_dir) if e5_on_disk else None,
            load_status="available" if (e5_cached or e5_on_disk) else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=e5_cached or e5_on_disk,
            parameters="118M",
            embedding_size=768,
            hidden_size=768,
            description="E5 (EmbEddings from bidirEctional Encoder rEpresentations) — contrastive learned embeddings.",
            advantages=["Contrastive pre-training", "Strong on similarity tasks"],
            weaknesses=["Requires query/passage prefix", "Highest false positive rate"],
            recommended_use="When maximum recall for semantic matches is needed",
        )
    )

    # E5-quora-finetuned (was missing from registry!)
    entries.append(
        ModelRegistryEntry(
            display_name="E5-quora-finetuned",
            internal_id="e5_ft",
            model_tier="research",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="local",
            version="phase2",
            local_path=str(paths.finetuned_e5_dir) if e5_ft_on_disk else None,
            cache_path=None,
            device="cpu",
            size_mb=_get_directory_size_mb(paths.finetuned_e5_dir) if e5_ft_on_disk else None,
            load_status="loaded" if e5_ft_on_disk else "missing",
            is_loaded=e5_ft_on_disk,
            has_artifacts=e5_ft_on_disk,
            parameters="118M",
            embedding_size=768,
            hidden_size=768,
            description="E5 fine-tuned on Quora duplicate detection data. Best performing bi-encoder for this task.",
            advantages=["Fine-tuned for task", "Highest bi-encoder accuracy", "Good generalization"],
            weaknesses=["Slower than base E5", "Larger model size"],
            recommended_use="Primary bi-encoder for semantic duplicate detection",
        )
    )

    # MPNet-base-v2
    mpnet_on_disk = paths.mpnet_model_dir.exists()
    entries.append(
        ModelRegistryEntry(
            display_name="MPNet-base-v2",
            internal_id="mpnet",
            model_tier="research",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.mpnet_model_dir) if mpnet_on_disk else None,
            cache_path=_get_hf_cache_path("sentence-transformers/all-mpnet-base-v2"),
            device="cpu",
            size_mb=_get_directory_size_mb(paths.mpnet_model_dir) if mpnet_on_disk else None,
            load_status="available" if (mpnet_cached or mpnet_on_disk) else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=mpnet_cached or mpnet_on_disk,
            parameters="110M",
            embedding_size=768,
            hidden_size=768,
            description="MPNet — masked and permuted language modeling. Best overall bi-encoder for this task.",
            advantages=["Best discrimination among bi-encoders", "Robust predictions"],
            weaknesses=["Slightly slower than BGE", "Still over-predicts on similar topics"],
            recommended_use="Primary bi-encoder for semantic duplicate detection",
        )
    )

    # DeBERTa-v3 Cross-Encoder (fixed hidden_size from 1024 to 768)
    deberta_on_disk = paths.deberta_model_dir.exists()
    entries.append(
        ModelRegistryEntry(
            display_name="DeBERTa-v3 Cross-Encoder",
            internal_id="deberta",
            model_tier="experimental",
            model_type="cross-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.deberta_model_dir) if deberta_on_disk else None,
            cache_path=_get_hf_cache_path("cross-encoder/nli-deberta-v3-base"),
            device="cpu",
            size_mb=_get_directory_size_mb(paths.deberta_model_dir) if deberta_on_disk else None,
            load_status="available" if (deberta_cached or deberta_on_disk) else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=deberta_cached or deberta_on_disk,
            parameters="184M",
            embedding_size=768,
            hidden_size=768,
            description="DeBERTa-v3 NLI cross-encoder. Uses entailment ratio for pairwise scoring.",
            advantages=["Joint encoding captures full context", "Best accuracy on test suite"],
            weaknesses=["NLI model, not trained for duplicate detection", "Slowest inference (~400ms)"],
            recommended_use="When accuracy is critical; works best in ensemble",
        )
    )

    # Cross-Encoder-Quora (Trained) — was missing from registry!
    ce_quora_size = _get_directory_size_mb(paths.finetuned_cross_encoder_dir) if ce_quora_on_disk else None
    entries.append(
        ModelRegistryEntry(
            display_name="Cross-Encoder-Quora (Trained)",
            internal_id="ce_quora",
            model_tier="production",
            model_type="cross-encoder",
            framework="sentence-transformers",
            source="local",
            version="phase2",
            local_path=str(paths.finetuned_cross_encoder_dir) if ce_quora_on_disk else None,
            cache_path=None,
            device="cpu",
            size_mb=ce_quora_size,
            load_status="loaded" if ce_quora_on_disk else "missing",
            is_loaded=ce_quora_on_disk,
            has_artifacts=ce_quora_on_disk,
            parameters="184M",
            embedding_size=768,
            hidden_size=768,
            description="Cross-Encoder fine-tuned on Quora duplicate detection data. Highest single-model accuracy.",
            advantages=["Fine-tuned for task", "Joint encoding", "Best single-model accuracy"],
            weaknesses=["Slowest inference", "Cannot precompute embeddings"],
            recommended_use="Default choice for accuracy-critical predictions",
        )
    )

    # Semantic Ensemble
    entries.append(
        ModelRegistryEntry(
            display_name="Semantic Ensemble",
            internal_id="ensemble",
            model_tier="experimental",
            model_type="ensemble",
            framework="ensemble",
            source="built-in",
            version="ensemble",
            local_path=None,
            cache_path=None,
            device="cpu",
            size_mb=None,
            load_status="loaded",
            is_loaded=True,
            has_artifacts=True,
            parameters="Varies (all models)",
            description="Adaptive weighted ensemble combining all models with dynamic feature-based weights.",
            advantages=["Best overall accuracy", "Handles all pair types", "Robust via trimmed mean"],
            weaknesses=["Slowest inference (loads all models)", "Depends on all sub-models"],
            recommended_use="Default choice for all predictions. Highest quality.",
        )
    )

    for entry in entries:
        entry.health_status, entry.health_reason = _map_health(entry.load_status, entry.has_artifacts, entry.is_loaded)

    return entries


def get_registry_dict(paths: AppPaths | None = None) -> list[dict[str, Any]]:
    entries = build_registry(paths)
    return [
        {
            "display_name": e.display_name,
            "internal_id": e.internal_id,
            "model_type": e.model_type,
            "framework": e.framework,
            "source": e.source,
            "version": e.version,
            "device": e.device,
            "size_mb": f"{e.size_mb:.1f}" if e.size_mb else "N/A",
            "load_status": e.load_status,
            "is_loaded": "✅" if e.is_loaded else "❌",
            "has_artifacts": "✅" if e.has_artifacts else "❌",
            "parameters": e.parameters,
            "embedding_size": e.embedding_size,
            "hidden_size": e.hidden_size,
            "avg_latency_ms": f"{e.avg_latency_ms:.0f}" if e.avg_latency_ms else "N/A",
            "description": e.description,
            "advantages": e.advantages,
            "weaknesses": e.weaknesses,
            "recommended_use": e.recommended_use,
            "local_path": e.local_path,
            "cache_path": e.cache_path,
        }
        for e in entries
    ]


def find_registry_entry(display_name: str, paths: AppPaths | None = None) -> ModelRegistryEntry | None:
    for entry in build_registry(paths):
        if entry.display_name == display_name:
            return entry
    return None
