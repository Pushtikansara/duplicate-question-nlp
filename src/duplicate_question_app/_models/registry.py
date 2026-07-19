"""Model Registry — tracks every model in the system with complete metadata.

Provides a single source of truth for model discovery, status checking,
and metadata queries used by the Streamlit UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from duplicate_question_app.config import AppPaths, get_app_paths, get_config
from duplicate_question_app.week2_inference import check_week2_artifacts


@dataclass
class ModelRegistryEntry:
    """Complete metadata for a single model."""

    display_name: str
    internal_id: str  # e.g. "week2_lr", "bge"
    model_type: str  # "classical-ml", "transformer", "bi-encoder", "cross-encoder", "ensemble"
    framework: str  # "joblib", "pytorch", "sentence-transformers", "ensemble"
    source: str  # "local" (trained), "huggingface" (downloaded), "built-in" (ensemble)
    version: str  # e.g. "week2", "week3", "phase2", "ensemble"
    local_path: str | None  # Path on disk if local
    cache_path: str | None  # HF cache path if applicable
    device: str  # "cpu" or "cuda"
    size_mb: float | None  # Model size on disk
    load_status: str  # "loaded", "available", "missing", "downloading"
    is_loaded: bool  # Currently loaded in memory
    has_artifacts: bool  # Files exist on disk
    parameters: str = "N/A"  # Parameter count
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


def _get_directory_size_mb(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024) if total else None


def _get_hf_cache_path(model_key: str) -> str | None:
    """Get HuggingFace cache path if model is cached."""
    try:
        from huggingface_hub import scan_cache_dir

        cache = scan_cache_dir()
        for repo in cache.repos:
            if model_key.replace("/", "--") in str(repo.repo_id) or model_key in str(repo.repo_id):
                return str(repo.repo_path)
    except (OSError, ImportError):
        pass
    # Try common cache locations with config overrides
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
    """Build the complete model registry by inspecting all available models."""
    if paths is None:
        from pathlib import Path

        paths = get_app_paths(Path(__file__).resolve().parents[2])

    week2_arts = check_week2_artifacts(paths)
    week2_ready = all(week2_arts.values())
    resolution = None
    try:
        from duplicate_question_app.config import resolve_model_selection

        resolution = resolve_model_selection(paths)
    except (FileNotFoundError, RuntimeError):
        pass

    # Check HF cache for sentence transformer models
    bge_cached = _get_hf_cache_path("BAAI/bge-base-en-v1.5") is not None
    e5_cached = _get_hf_cache_path("intfloat/e5-base-v2") is not None
    mpnet_cached = _get_hf_cache_path("sentence-transformers/all-mpnet-base-v2") is not None
    deberta_cached = _get_hf_cache_path("cross-encoder/nli-deberta-v3-base") is not None

    entries: list[ModelRegistryEntry] = []

    # Week 2 - Logistic Regression
    lr_path = paths.models_dir / "week2_models" / "logistic_regression.joblib"
    svm_path = paths.models_dir / "week2_models" / "linear_svm.joblib"
    paths.models_dir / "week2_models" / "tfidf_vectorizer.joblib"

    entries.append(
        ModelRegistryEntry(
            display_name="TF-IDF + Logistic Regression (Week 2)",
            internal_id="week2_lr",
            model_type="classical-ml",
            framework="joblib",
            source="local",
            version="week2",
            local_path=str(lr_path) if lr_path.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=_get_directory_size_mb(paths.models_dir / "week2_models"),
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
            model_type="classical-ml",
            framework="joblib",
            source="local",
            version="week2",
            local_path=str(svm_path) if svm_path.exists() else None,
            cache_path=None,
            device="cpu",
            size_mb=_get_directory_size_mb(paths.models_dir / "week2_models"),
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
    entries.append(
        ModelRegistryEntry(
            display_name="BGE-base-en-v1.5",
            internal_id="bge",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.bge_model_dir) if paths.bge_model_dir.exists() else None,
            cache_path=_get_hf_cache_path("BAAI/bge-base-en-v1.5"),
            device="cpu",
            size_mb=None,
            load_status="available" if bge_cached else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=bge_cached or paths.bge_model_dir.exists(),
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
    entries.append(
        ModelRegistryEntry(
            display_name="E5-base-v2",
            internal_id="e5",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.e5_model_dir) if paths.e5_model_dir.exists() else None,
            cache_path=_get_hf_cache_path("intfloat/e5-base-v2"),
            device="cpu",
            size_mb=None,
            load_status="available" if e5_cached else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=e5_cached or paths.e5_model_dir.exists(),
            parameters="118M",
            embedding_size=768,
            hidden_size=768,
            description="E5 (EmbEddings from bidirEctional Encoder rEpresentations) — contrastive learned embeddings.",
            advantages=["Contrastive pre-training", "Strong on similarity tasks"],
            weaknesses=["Requires query/passage prefix", "Highest false positive rate"],
            recommended_use="When maximum recall for semantic matches is needed",
        )
    )

    # MPNet-base-v2
    entries.append(
        ModelRegistryEntry(
            display_name="MPNet-base-v2",
            internal_id="mpnet",
            model_type="bi-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.mpnet_model_dir) if paths.mpnet_model_dir.exists() else None,
            cache_path=_get_hf_cache_path("sentence-transformers/all-mpnet-base-v2"),
            device="cpu",
            size_mb=None,
            load_status="available" if mpnet_cached else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=mpnet_cached or paths.mpnet_model_dir.exists(),
            parameters="110M",
            embedding_size=768,
            hidden_size=768,
            description="MPNet — masked and permuted language modeling. Best overall bi-encoder for this task.",
            advantages=["Best discrimination among bi-encoders", "Robust predictions"],
            weaknesses=["Slightly slower than BGE", "Still over-predicts on similar topics"],
            recommended_use="Primary bi-encoder for semantic duplicate detection",
        )
    )

    # DeBERTa-v3 Cross-Encoder
    entries.append(
        ModelRegistryEntry(
            display_name="DeBERTa-v3 Cross-Encoder",
            internal_id="deberta",
            model_type="cross-encoder",
            framework="sentence-transformers",
            source="huggingface",
            version="phase2",
            local_path=str(paths.deberta_model_dir) if paths.deberta_model_dir.exists() else None,
            cache_path=_get_hf_cache_path("cross-encoder/nli-deberta-v3-base"),
            device="cpu",
            size_mb=None,
            load_status="available" if deberta_cached else "missing (auto-download)",
            is_loaded=False,
            has_artifacts=deberta_cached or paths.deberta_model_dir.exists(),
            parameters="184M",
            embedding_size=1024,
            hidden_size=1024,
            description="DeBERTa-v3 NLI cross-encoder. Uses entailment ratio for pairwise scoring.",
            advantages=["Joint encoding captures full context", "Best accuracy on test suite"],
            weaknesses=["NLI model, not trained for duplicate detection", "Slowest inference (~400ms)"],
            recommended_use="When accuracy is critical; works best in ensemble",
        )
    )

    # Semantic Ensemble
    entries.append(
        ModelRegistryEntry(
            display_name="Semantic Ensemble",
            internal_id="ensemble",
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
            description="Adaptive weighted ensemble combining all 8 models with dynamic feature-based weights.",
            advantages=["Best overall accuracy", "Handles all pair types", "Robust via trimmed mean"],
            weaknesses=["Slowest inference (loads all models)", "Depends on all sub-models"],
            recommended_use="Default choice for all predictions. Highest quality.",
        )
    )

    return entries


def get_registry_dict(paths: AppPaths | None = None) -> list[dict[str, Any]]:
    """Get registry as serializable dicts for display."""
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
        }
        for e in entries
    ]


def find_registry_entry(display_name: str, paths: AppPaths | None = None) -> ModelRegistryEntry | None:
    """Find a registry entry by display name."""
    for entry in build_registry(paths):
        if entry.display_name == display_name:
            return entry
    return None
