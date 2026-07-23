from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from ares.api.dependencies import (
    apply_rate_limit,
    get_security_manager,
    get_token_data,
)
from ares.api.models import UserRole
from ares.api.security import SecurityManager

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(apply_rate_limit)])


@router.post("/token")
async def create_token(
    x_api_key: str,
    sm: Annotated[SecurityManager, Depends(get_security_manager)],
) -> dict[str, Any]:
    token_data = sm.authenticate_request(api_key=x_api_key)
    access_token = sm.create_access_token(subject=token_data["sub"], role=UserRole(token_data["role"]))
    refresh_token = sm.create_refresh_token(subject=token_data["sub"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    sm: Annotated[SecurityManager, Depends(get_security_manager)],
) -> dict[str, Any]:
    try:
        new_access = sm.jwt.refresh_access_token(refresh_token)
        return {"access_token": new_access, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.get("/verify")
async def verify_token(
    token: Annotated[dict[str, Any], Depends(get_token_data)],
) -> dict[str, Any]:
    return {
        "sub": token.get("sub"),
        "role": token.get("role"),
        "permissions": token.get("permissions", []),
        "type": token.get("type", "access"),
    }
