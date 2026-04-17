from __future__ import annotations

import base64
import posixpath
from typing import Any, Dict

from app.config import runtime_state, settings
from app.core.docker import get_docker_service
from app.core.errors import ToolError
from app.core.security import validate_command

__all__ = [
    "ToolError",
    "shell_exec",
    "upload_file",
    "read_file",
]


def _active_container() -> str:
    active = runtime_state.get_active_container()
    if not active:
        raise ToolError("no active container set")
    return active


def _safe_workspace_path(path: str) -> str:
    target = posixpath.normpath(posixpath.join(settings.workspace_dir, path.lstrip("/")))
    workspace_prefix = settings.workspace_dir.rstrip("/") + "/"
    if not (target == settings.workspace_dir or target.startswith(workspace_prefix)):
        raise ToolError("path must stay within workspace")
    return target


def shell_exec(cmd: str, timeout: int | None = None) -> Dict[str, Any]:
    """Execute a shell command inside the active Kali container. Returns exit_code and combined stdout/stderr output."""
    validate_command(cmd)
    active = _active_container()
    result = get_docker_service().exec(active, cmd, timeout or settings.command_timeout_seconds)
    return {"exit_code": result.exit_code, "output": result.output, "container": active}


def upload_file(name: str, b64: str) -> Dict[str, Any]:
    """Upload a file to /tmp/workspace/ in the active container. name is the filename; b64 is base64-encoded content."""
    active = _active_container()
    target = _safe_workspace_path(name)
    try:
        content = base64.b64decode(b64)
    except Exception as exc:
        raise ToolError("invalid base64 payload") from exc
    get_docker_service().write_file(active, target, content)
    return {"message": "uploaded", "path": target, "container": active}


def read_file(path: str) -> Dict[str, Any]:
    """Read a file from /tmp/workspace/ in the active container. path is relative to the workspace."""
    active = _active_container()
    target = _safe_workspace_path(path)
    content = get_docker_service().read_file(active, target)
    return {"path": target, "content": content, "container": active}
