from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ares.api.dependencies import get_request_id, require_admin
from ares.api.models import ConfigResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config", response_model=ConfigResponse, dependencies=[Depends(require_admin)])
async def get_config(
    section: str | None = None,
    verbose: bool = False,
    request_id: str = Depends(get_request_id),
) -> ConfigResponse:
    from duplicate_question_app._config.loader import load_all_configs

    try:
        all_config = load_all_configs()
        if section:
            if section not in all_config:
                raise HTTPException(status_code=404, detail=f"Config section '{section}' not found")
            sections = {section: all_config[section]}
        else:
            sections = (
                all_config
                if verbose
                else {k: v for k, v in all_config.items() if k in ("app", "paths", "inference", "logging")}
            )
        return ConfigResponse(
            sections=sections,
            source="yaml",
            request_id=request_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/config/validate", dependencies=[Depends(require_admin)])
async def validate_config(
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    config_dir = Path.cwd() / "configs"
    if not config_dir.exists():
        errors.append("configs/ directory not found")
    else:
        yaml_files = list(config_dir.glob("*.yaml"))
        if not yaml_files:
            warnings.append("No YAML config files found")
        for yf in yaml_files:
            try:
                import yaml

                with open(yf) as f:
                    yaml.safe_load(f)
            except Exception as e:
                errors.append(f"{yf.name}: {e}")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "request_id": request_id,
    }
