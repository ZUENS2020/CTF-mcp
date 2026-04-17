from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from app.core.bore import get_bore_manager

router = APIRouter(tags=["tunnels"])


@router.get("/api/tunnels")
def list_tunnels() -> Dict[str, List[Dict[str, Any]]]:
    return {"tunnels": get_bore_manager().list_tunnels()}
