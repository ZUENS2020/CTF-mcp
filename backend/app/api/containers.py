from __future__ import annotations

from typing import Dict

from docker.errors import APIError, NotFound
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import runtime_state, settings
from app.core.docker import get_docker_service

router = APIRouter(prefix="/api/containers", tags=["containers"])


class CreateContainerRequest(BaseModel):
    name: str
    image: str | None = None


@router.get("")
def list_containers() -> list[dict]:
    try:
        return get_docker_service().list_containers()
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("")
def create_container(payload: CreateContainerRequest) -> Dict[str, str]:
    image = payload.image or settings.docker_base_image
    try:
        result = get_docker_service().create_container(payload.name, image)
        return {"message": "created", **result}
    except APIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{name}")
def delete_container(name: str) -> Dict[str, str]:
    try:
        get_docker_service().delete_container(name)
        if runtime_state.get_active_container() == name:
            runtime_state.set_active_container("")
        return {"message": "deleted", "name": name}
    except NotFound as exc:
        raise HTTPException(status_code=404, detail="container not found") from exc
    except APIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{name}/activate")
def activate_container(name: str) -> Dict[str, str]:
    try:
        get_docker_service().get_container(name)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail="container not found") from exc

    runtime_state.set_active_container(name)
    return {"message": "active container set", "name": name}


@router.get("/active")
def get_active_container() -> Dict[str, str | None]:
    active = runtime_state.get_active_container() or None
    return {"active_container": active}
