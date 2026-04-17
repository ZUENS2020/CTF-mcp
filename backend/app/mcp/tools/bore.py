from __future__ import annotations

from typing import Any, Dict

from app.core.bore import get_bore_manager

from .shell import ToolError


def _validate_port(local_port: int) -> None:
    if not isinstance(local_port, int):
        raise ToolError("local_port must be an integer")
    if local_port < 1 or local_port > 65535:
        raise ToolError("local_port must be in range 1-65535")


def start_bore(local_port: int, server: str | None = None) -> Dict[str, Any]:
    _validate_port(local_port)
    try:
        state = get_bore_manager().start_tunnel(local_port=local_port, server=server)
    except RuntimeError as exc:
        raise ToolError(str(exc)) from exc
    return state.to_dict()


def stop_bore(local_port: int) -> Dict[str, Any]:
    _validate_port(local_port)
    try:
        state = get_bore_manager().stop_tunnel(local_port=local_port)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    return state.to_dict()


def list_bore_tunnels() -> Dict[str, Any]:
    return {"tunnels": get_bore_manager().list_tunnels()}
