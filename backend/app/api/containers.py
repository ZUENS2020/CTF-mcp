from __future__ import annotations

import asyncio
from typing import Dict

from docker.errors import APIError, DockerException, NotFound
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.docker import get_docker_service

router = APIRouter(prefix="/api/containers", tags=["containers"])


class CreateContainerRequest(BaseModel):
    name: str
    image: str | None = None


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


@router.get("")
async def list_containers() -> list[dict]:
    try:
        return await _run_docker_call(get_docker_service().list_containers)
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("")
async def create_container(payload: CreateContainerRequest) -> Dict[str, str]:
    image = payload.image or settings.docker_base_image
    try:
        result = await _run_docker_call(get_docker_service().create_container, payload.name, image)
        return {"message": "created", **result}
    except APIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{name}")
async def delete_container(name: str) -> Dict[str, str]:
    try:
        await _run_docker_call(get_docker_service().delete_container, name)
        return {"message": "deleted", "name": name}
    except NotFound as exc:
        raise HTTPException(status_code=404, detail="container not found") from exc
    except APIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
