from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from duplicate_question_app._config.loader import (
    ENV_PREFIX,
)
from duplicate_question_app._config.loader import get_config as _loader_get_config

# Re-export for consumer convenience
get_config = _loader_get_config


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    data_dir: Path
    models_dir: Path
    results_dir: Path
    notebooks_dir: Path
    week3_model_dir: Path
    week4_model_dir: Path
    transformer_results_dir: Path
    week4_results_dir: Path
    baseline_results_dir: Path
    bge_model_dir: Path
    e5_model_dir: Path
    mpnet_model_dir: Path
    deberta_model_dir: Path
    finetuned_e5_dir: Path
    finetuned_bge_dir: Path
    finetuned_cross_encoder_dir: Path


@dataclass(frozen=True)
class ModelDirectoryStatus:
    model_dir: Path
    label: str
    exists: bool
    has_config: bool
    weight_file: Path | None
    has_tokenizer: bool
    tokenizer_files: tuple[str, ...]
    ready: bool
    issues: tuple[str, ...]
    fingerprint: str


@dataclass(frozen=True)
class ModelResolution:
    week3: ModelDirectoryStatus
    week4: ModelDirectoryStatus
    selected_model_dir: Path
    selected_label: str
    selected_version: str
    fallback_reason: str | None
    cache_key: str


def _resolve_override(key: str) -> str | None:
    env_key = f"{ENV_PREFIX}{key.upper()}"
    return os.environ.get(env_key)


def _default_project_root() -> Path:
    """Compute project root from file location.

    settings.py is at src/duplicate_question_app/_config/settings.py.
    parents[3] reaches the project root (3 levels up from _config/).
    """
    return Path(__file__).resolve().parents[3]


def get_app_paths(project_root: Path | None = None) -> AppPaths:
    root = project_root or _default_project_root()

    env_root = _resolve_override("PROJECT_ROOT")
    if env_root:
        root = Path(env_root)

    paths_cfg = get_config("paths")
    if not paths_cfg:
        return _legacy_get_app_paths(root)

    def _resolve_path(key: str) -> Path:
        override = _resolve_override(key)
        if override:
            p = Path(override)
            return p if p.is_absolute() else root / p
        val = paths_cfg.get(key)
        if val is None:
            return root
        p = Path(str(val))
        return p if p.is_absolute() else root / p

    return AppPaths(
        project_root=root,
        data_dir=_resolve_path("data_dir"),
        models_dir=_resolve_path("models_dir"),
        results_dir=_resolve_path("results_dir"),
        notebooks_dir=_resolve_path("notebooks_dir"),
        week3_model_dir=_resolve_path("week3_model_dir"),
        week4_model_dir=_resolve_path("week4_model_dir"),
        transformer_results_dir=_resolve_path("transformer_results_dir"),
        week4_results_dir=_resolve_path("week4_results_dir"),
        baseline_results_dir=_resolve_path("baseline_results_dir"),
        bge_model_dir=_resolve_path("bge_model_dir"),
        e5_model_dir=_resolve_path("e5_model_dir"),
        mpnet_model_dir=_resolve_path("mpnet_model_dir"),
        deberta_model_dir=_resolve_path("deberta_model_dir"),
        finetuned_e5_dir=_resolve_path("finetuned_e5_dir"),
        finetuned_bge_dir=_resolve_path("finetuned_bge_dir"),
        finetuned_cross_encoder_dir=_resolve_path("finetuned_cross_encoder_dir"),
    )


def _legacy_get_app_paths(root: Path | None = None) -> AppPaths:
    """Fallback when configs/ is unavailable — matches original hardcoded values."""
    if root is None:
        root = _default_project_root()
    return AppPaths(
        project_root=root,
        data_dir=root / "data",
        models_dir=root / "models",
        results_dir=root / "outputs",
        notebooks_dir=root / "notebooks",
        week3_model_dir=root / "models" / "saved_transformer_model",
        week4_model_dir=root / "models" / "week4_improved_model",
        transformer_results_dir=root / "outputs" / "transformer_model",
        week4_results_dir=root / "outputs" / "week4_improvement",
        baseline_results_dir=root / "outputs" / "baseline_model",
        bge_model_dir=root / "models" / "bge_base_en_v1_5",
        e5_model_dir=root / "models" / "e5_base_v2",
        mpnet_model_dir=root / "models" / "mpnet_base_v2",
        deberta_model_dir=root / "models" / "deberta_v3_cross_encoder",
        finetuned_e5_dir=root / "models" / "e5-quora-finetuned",
        finetuned_bge_dir=root / "models" / "bge-quora-finetuned",
        finetuned_cross_encoder_dir=root / "models" / "cross-encoder-quora",
    )


def _build_fingerprint(paths: list[Path]) -> str:
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return "missing"

    payload = "|".join(
        f"{path.name}:{path.stat().st_size}:{path.stat().st_mtime_ns}" for path in sorted(existing_paths)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def inspect_model_dir(model_dir: Path, label: str) -> ModelDirectoryStatus:
    config_path = model_dir / "config.json"
    weight_file = next(
        (
            model_dir / filename
            for filename in ("model.safetensors", "pytorch_model.bin")
            if (model_dir / filename).exists()
        ),
        None,
    )
    if weight_file is None:
        weight_file = next(
            (
                model_dir / filename
                for filename in ("pytorch_model.bin", "model.safetensors")
                if (model_dir / filename).exists()
            ),
            None,
        )
    tokenizer_candidates = tuple(
        filename
        for filename in (
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "sentencepiece.bpe.model",
        )
        if (model_dir / filename).exists()
    )
    has_tokenizer = bool(tokenizer_candidates)

    issues: list[str] = []
    if not model_dir.exists():
        issues.append("directory is missing")
    if model_dir.exists() and not config_path.exists():
        issues.append("config.json is missing")
    if model_dir.exists() and weight_file is None:
        issues.append("model weights are missing")
    if model_dir.exists() and not has_tokenizer:
        issues.append("tokenizer files are missing")

    fingerprint = _build_fingerprint(
        [
            config_path,
            *(model_dir / filename for filename in tokenizer_candidates),
            *(model_dir / filename for filename in ("model.safetensors", "pytorch_model.bin")),
        ]
    )

    return ModelDirectoryStatus(
        model_dir=model_dir,
        label=label,
        exists=model_dir.exists(),
        has_config=config_path.exists(),
        weight_file=weight_file,
        has_tokenizer=has_tokenizer,
        tokenizer_files=tokenizer_candidates,
        ready=model_dir.exists() and config_path.exists() and weight_file is not None and has_tokenizer,
        issues=tuple(issues),
        fingerprint=fingerprint,
    )


def model_dir_has_artifacts(model_dir: Path) -> bool:
    status = inspect_model_dir(model_dir, label=model_dir.name)
    return status.ready


def resolve_model_selection(paths: AppPaths) -> ModelResolution:
    week4 = inspect_model_dir(paths.week4_model_dir, "Week 4 Improved DistilBERT")
    week3 = inspect_model_dir(paths.week3_model_dir, "Week 3 DistilBERT")

    selected = week4 if week4.ready else week3
    fallback_reason: str | None = None
    if not week4.ready:
        if week4.issues:
            fallback_reason = "Week 4 artifacts are incomplete: " + ", ".join(week4.issues) + "."
        else:
            fallback_reason = "Week 4 artifacts are unavailable."

    cache_key = "|".join(
        [
            f"week4:{week4.fingerprint}",
            f"week3:{week3.fingerprint}",
            f"selected:{selected.model_dir.name}",
        ]
    )

    return ModelResolution(
        week3=week3,
        week4=week4,
        selected_model_dir=selected.model_dir,
        selected_label=selected.label,
        selected_version="week4" if selected.model_dir == paths.week4_model_dir else "week3",
        fallback_reason=fallback_reason if selected.model_dir == paths.week3_model_dir else None,
        cache_key=cache_key,
    )


def resolve_preferred_model_dir(paths: AppPaths) -> Path:
    return resolve_model_selection(paths).selected_model_dir


# ---------------------------------------------------------------------------
# Model registry — loaded from YAML with env override support
# ---------------------------------------------------------------------------


def _load_model_choices() -> list[str]:
    cfg = get_config("models")
    if cfg and "model_choices" in cfg:
        return list(cfg["model_choices"])
    return _LEGACY_MODEL_CHOICES


def _load_model_version_short() -> dict[str, str]:
    cfg = get_config("models")
    if cfg and "model_version_short" in cfg:
        return dict(cfg["model_version_short"])
    return _LEGACY_MODEL_VERSION_SHORT


def _load_transformer_models() -> frozenset[str]:
    cfg = get_config("models")
    if cfg and "backends" in cfg and "transformer_models" in cfg["backends"]:
        return frozenset(cfg["backends"]["transformer_models"])
    return _LEGACY_TRANSFORMER_MODELS


def _load_sentence_transformer_models() -> frozenset[str]:
    cfg = get_config("models")
    if cfg and "backends" in cfg and "sentence_transformer_models" in cfg["backends"]:
        return frozenset(cfg["backends"]["sentence_transformer_models"])
    return _LEGACY_SENTENCE_TRANSFORMER_MODELS


def _load_cross_encoder_models() -> frozenset[str]:
    cfg = get_config("models")
    if cfg and "backends" in cfg and "cross_encoder_models" in cfg["backends"]:
        return frozenset(cfg["backends"]["cross_encoder_models"])
    return _LEGACY_CROSS_ENCODER_MODELS


def _load_finetuned_embedding_models() -> frozenset[str]:
    cfg = get_config("models")
    if cfg and "backends" in cfg and "finetuned_embedding_models" in cfg["backends"]:
        return frozenset(cfg["backends"]["finetuned_embedding_models"])
    return _LEGACY_FINETUNED_EMBEDDING_MODELS


def _load_hub_name(model_key: str) -> str | None:
    cfg = get_config("models")
    if cfg and "hub_names" in cfg:
        return cfg["hub_names"].get(model_key)
    return None


# Legacy fallback values (identical to original hardcoded values)
_LEGACY_MODEL_CHOICES: list[str] = [
    "TF-IDF + Logistic Regression (Week 2)",
    "TF-IDF + Linear SVM (Week 2)",
    "DistilBERT (Week 3)",
    "Improved DistilBERT (Week 4)",
    "BGE-base-en-v1.5",
    "E5-base-v2",
    "E5-quora-finetuned",
    "MPNet-base-v2",
    "DeBERTa-v3 Cross-Encoder",
    "Cross-Encoder-Quora (Trained)",
    "Semantic Ensemble",
]

_LEGACY_MODEL_VERSION_SHORT: dict[str, str] = {
    "TF-IDF + Logistic Regression (Week 2)": "week2_lr",
    "TF-IDF + Linear SVM (Week 2)": "week2_svm",
    "DistilBERT (Week 3)": "week3",
    "Improved DistilBERT (Week 4)": "week4",
    "BGE-base-en-v1.5": "bge",
    "E5-base-v2": "e5",
    "E5-quora-finetuned": "e5_ft",
    "MPNet-base-v2": "mpnet",
    "DeBERTa-v3 Cross-Encoder": "deberta",
    "Cross-Encoder-Quora (Trained)": "ce_quora",
    "Semantic Ensemble": "ensemble",
}

_LEGACY_TRANSFORMER_MODELS = frozenset(
    {
        "DistilBERT (Week 3)",
        "Improved DistilBERT (Week 4)",
    }
)

_LEGACY_SENTENCE_TRANSFORMER_MODELS = frozenset(
    {
        "BGE-base-en-v1.5",
        "E5-base-v2",
        "E5-quora-finetuned",
        "MPNet-base-v2",
    }
)

_LEGACY_FINETUNED_EMBEDDING_MODELS = frozenset(
    {
        "E5-quora-finetuned",
    }
)

_LEGACY_CROSS_ENCODER_MODELS = frozenset(
    {
        "DeBERTa-v3 Cross-Encoder",
        "Cross-Encoder-Quora (Trained)",
    }
)

# Module-level constants populated lazily from config
MODEL_CHOICES: list[str] = _LEGACY_MODEL_CHOICES
MODEL_VERSION_SHORT: dict[str, str] = _LEGACY_MODEL_VERSION_SHORT
TRANSFORMER_MODELS: frozenset[str] = _LEGACY_TRANSFORMER_MODELS
SENTENCE_TRANSFORMER_MODELS: frozenset[str] = _LEGACY_SENTENCE_TRANSFORMER_MODELS
FINETUNED_EMBEDDING_MODELS: frozenset[str] = _LEGACY_FINETUNED_EMBEDDING_MODELS
CROSS_ENCODER_MODELS: frozenset[str] = _LEGACY_CROSS_ENCODER_MODELS


def _reload_module_constants() -> None:
    """Reload model constants from YAML config. Called once at startup."""
    global MODEL_CHOICES, MODEL_VERSION_SHORT
    global TRANSFORMER_MODELS, SENTENCE_TRANSFORMER_MODELS
    global FINETUNED_EMBEDDING_MODELS, CROSS_ENCODER_MODELS

    choices = _load_model_choices()
    if choices != _LEGACY_MODEL_CHOICES:
        MODEL_CHOICES = choices

    version_short = _load_model_version_short()
    if version_short != _LEGACY_MODEL_VERSION_SHORT:
        MODEL_VERSION_SHORT = version_short

    tf = _load_transformer_models()
    if tf != _LEGACY_TRANSFORMER_MODELS:
        TRANSFORMER_MODELS = tf

    st = _load_sentence_transformer_models()
    if st != _LEGACY_SENTENCE_TRANSFORMER_MODELS:
        SENTENCE_TRANSFORMER_MODELS = st

    ce = _load_cross_encoder_models()
    if ce != _LEGACY_CROSS_ENCODER_MODELS:
        CROSS_ENCODER_MODELS = ce

    ft = _load_finetuned_embedding_models()
    if ft != _LEGACY_FINETUNED_EMBEDDING_MODELS:
        FINETUNED_EMBEDDING_MODELS = ft


# Load config on first import
_reload_module_constants()


def is_transformer_model(model_name: str) -> bool:
    return model_name in TRANSFORMER_MODELS


def is_sentence_transformer_model(model_name: str) -> bool:
    return model_name in SENTENCE_TRANSFORMER_MODELS


def is_cross_encoder_model(model_name: str) -> bool:
    return model_name in CROSS_ENCODER_MODELS


def is_ensemble_model(model_name: str) -> bool:
    return model_name == "Semantic Ensemble"


def is_finetuned_embedding_model(model_name: str) -> bool:
    return model_name in FINETUNED_EMBEDDING_MODELS


def is_new_embedding_model(model_name: str) -> bool:
    return model_name in SENTENCE_TRANSFORMER_MODELS | CROSS_ENCODER_MODELS | FINETUNED_EMBEDDING_MODELS | {
        "Semantic Ensemble"
    }


@dataclass
class ModelMetrics:
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    source: str = ""


@dataclass
class FullModelInfo:
    display_name: str
    version_key: str
    week: str
    description: str
    metrics: ModelMetrics
    is_transformer: bool
