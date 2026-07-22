from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ares.api.dependencies import get_request_id, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_plugin_manager():
    from ares.plugins.manager import PluginManager

    return PluginManager()


@router.get("/plugins", dependencies=[Depends(require_admin)])
async def list_plugins(
    request_id: str = Depends(get_request_id),
) -> list[dict[str, Any]]:
    pm = _get_plugin_manager()
    try:
        plugins = pm.list()
        return [p.to_dict() if hasattr(p, "to_dict") else {"id": str(p)} for p in plugins]
    except Exception as e:
        logger.warning("Plugin list failed: %s", e)
        return []


@router.get("/plugins/{plugin_id}", dependencies=[Depends(require_admin)])
async def get_plugin(
    plugin_id: str,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    pm = _get_plugin_manager()
    try:
        plugin = pm.get(plugin_id) if hasattr(pm, "get") else None
        if plugin is None:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
        return plugin.to_dict() if hasattr(plugin, "to_dict") else {"id": plugin_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/plugins/{plugin_id}/enable", dependencies=[Depends(require_admin)])
async def enable_plugin(
    plugin_id: str,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    pm = _get_plugin_manager()
    try:
        if hasattr(pm, "enable"):
            pm.enable(plugin_id)
        return {"status": "ok", "plugin_id": plugin_id, "action": "enabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/plugins/{plugin_id}/disable", dependencies=[Depends(require_admin)])
async def disable_plugin(
    plugin_id: str,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    pm = _get_plugin_manager()
    try:
        if hasattr(pm, "disable"):
            pm.disable(plugin_id)
        return {"status": "ok", "plugin_id": plugin_id, "action": "disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/plugins/{plugin_id}", dependencies=[Depends(require_admin)])
async def uninstall_plugin(
    plugin_id: str,
    request_id: str = Depends(get_request_id),
) -> dict[str, Any]:
    pm = _get_plugin_manager()
    try:
        if hasattr(pm, "uninstall"):
            pm.uninstall(plugin_id)
        return {"status": "ok", "plugin_id": plugin_id, "action": "uninstalled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
