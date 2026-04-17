from __future__ import annotations

import asyncio
import posixpath
from typing import Dict

from docker.errors import APIError, DockerException, NotFound
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import runtime_state, settings
from app.core.docker import get_docker_service
from app.core.security import validate_command

router = APIRouter(prefix="/api/kali", tags=["kali"])


class ExecRequest(BaseModel):
    cmd: str = Field(min_length=1)
    timeout: int | None = Field(default=None, ge=1, le=3600)


class ReadRequest(BaseModel):
    path: str


async def _run_docker_call(fn, *args, timeout_seconds: int | None = None):
    timeout = timeout_seconds or settings.docker_operation_timeout_seconds
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=f"docker operation timed out after {timeout}s") from exc
    except APIError:
        raise
    except DockerException as exc:
        raise HTTPException(status_code=503, detail=f"docker unavailable: {exc}") from exc


def _active_container() -> str:
    active = runtime_state.get_active_container()
    if not active:
        raise HTTPException(status_code=400, detail="no active container set")
    return active


def _safe_workspace_path(path: str) -> str:
    target = posixpath.normpath(posixpath.join(settings.workspace_dir, path.lstrip("/")))
    workspace_prefix = settings.workspace_dir.rstrip("/") + "/"
    if not (target == settings.workspace_dir or target.startswith(workspace_prefix)):
        raise HTTPException(status_code=400, detail="path must stay within workspace")
    return target


@router.post("/exec")
async def exec_in_kali(payload: ExecRequest) -> Dict[str, str | int]:
    validate_command(payload.cmd)
    active = _active_container()
    command_timeout = payload.timeout or settings.command_timeout_seconds
    operation_timeout = max(settings.docker_operation_timeout_seconds, command_timeout + 5)

    try:
        result = await _run_docker_call(
            get_docker_service().exec,
            active,
            payload.cmd,
            command_timeout,
            timeout_seconds=operation_timeout,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail="active container not found") from exc
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "container": active,
        "exit_code": result.exit_code,
        "output": result.output,
    }


@router.post("/read")
async def read_in_kali(payload: ReadRequest) -> Dict[str, str]:
    active = _active_container()
    target = _safe_workspace_path(payload.path)

    try:
        content = await _run_docker_call(get_docker_service().read_file, active, target)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail="file or container not found") from exc
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "container": active,
        "path": target,
        "content": content,
    }
