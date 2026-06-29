from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


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


def get_app_paths(project_root: Path | None = None) -> AppPaths:
    root = project_root or Path(__file__).resolve().parents[2]
    return AppPaths(
        project_root=root,
        data_dir=root / "data",
        models_dir=root / "models",
        results_dir=root / "results",
        notebooks_dir=root / "notebooks",
        week3_model_dir=root / "models" / "saved_transformer_model",
        week4_model_dir=root / "models" / "week4_improved_model",
        transformer_results_dir=root / "results" / "transformer_model",
        week4_results_dir=root / "results" / "week4_improvement",
        baseline_results_dir=root / "results" / "baseline_model",
    )


def _build_fingerprint(paths: list[Path]) -> str:
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        return "missing"

    payload = "|".join(
        f"{path.name}:{path.stat().st_size}:{path.stat().st_mtime_ns}" for path in sorted(existing_paths)
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


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
            fallback_reason = (
                "Week 4 artifacts are incomplete: " + ", ".join(week4.issues) + "."
            )
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
