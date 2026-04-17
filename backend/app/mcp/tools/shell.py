from __future__ import annotations

import asyncio
import posixpath
from typing import Any, Dict

from docker.errors import DockerException

from app.config import runtime_state, settings
from app.core.docker import get_docker_service
from app.core.errors import ToolError
from app.core.security import validate_command

__all__ = [
    "ToolError",
    "shell_exec",
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


async def _run_docker_call(fn, *args, timeout_seconds: int | None = None):
    timeout = timeout_seconds or settings.docker_operation_timeout_seconds
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout)
    except TimeoutError as exc:
        raise ToolError(f"docker operation timed out after {timeout}s") from exc
    except DockerException as exc:
        raise ToolError(f"docker unavailable: {exc}") from exc


async def shell_exec(cmd: str, timeout: int | None = None) -> Dict[str, Any]:
    """Execute a shell command inside the active Kali container. Returns exit_code and combined stdout/stderr output."""
    validate_command(cmd)
    active = _active_container()
    command_timeout = timeout or settings.command_timeout_seconds
    operation_timeout = max(settings.docker_operation_timeout_seconds, command_timeout + 5)
    result = await _run_docker_call(
        get_docker_service().exec,
        active,
        cmd,
        command_timeout,
        timeout_seconds=operation_timeout,
    )
    return {"exit_code": result.exit_code, "output": result.output, "container": active}


async def read_file(path: str) -> Dict[str, Any]:
    """Read a file from /tmp/workspace/ in the active container. path is relative to the workspace."""
    active = _active_container()
    target = _safe_workspace_path(path)
    content = await _run_docker_call(get_docker_service().read_file, active, target)
    return {"path": target, "content": content, "container": active}
