from __future__ import annotations

import logging
import os
import platform
import sys
import time

import psutil
import torch
from fastapi import APIRouter, Depends

from ares.api.dependencies import get_request_id, require_admin
from ares.api.models import SystemInfoResponse
from ares.api.version import ARES_VERSION

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


@router.get("/system/info", response_model=SystemInfoResponse, dependencies=[Depends(require_admin)])
async def system_info(
    request_id: str = Depends(get_request_id),
) -> SystemInfoResponse:
    deps: dict[str, str] = {}
    for mod_name in [
        "torch",
        "transformers",
        "pandas",
        "numpy",
        "sklearn",
        "streamlit",
    ]:
        try:
            mod = __import__(mod_name)
            deps[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            deps[mod_name] = "not installed"
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    cuda_version = torch.version.cuda if gpu_available else None
    config_count = 0
    config_dir = os.path.join(os.getcwd(), "configs")
    if os.path.isdir(config_dir):
        config_count = len([f for f in os.listdir(config_dir) if f.endswith((".yaml", ".yml"))])
    plugin_count = 0
    try:
        from ares.plugins.manager import PluginManager

        pm = PluginManager()
        plugin_count = len(pm.list())
    except Exception:
        pass
    model_available = False
    try:
        from ares._engine import ARES

        engine = ARES()
        engine._lazy_load()
        model_available = engine._bundle is not None
    except Exception:
        pass
    return SystemInfoResponse(
        version=ARES_VERSION,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        cpu_cores=os.cpu_count() or 0,
        memory_gb=round(psutil.virtual_memory().total / (1024**3), 1),
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        cuda_version=cuda_version,
        torch_version=torch.__version__,
        dependencies=deps,
        config_file_count=config_count,
        model_available=model_available,
        plugins_loaded=plugin_count,
        uptime_seconds=time.time() - _start_time,
        request_id=request_id,
    )
