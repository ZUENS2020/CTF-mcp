from __future__ import annotations

import io
import shlex
import tarfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import docker
from docker.errors import APIError, NotFound

from app.config import settings


@dataclass
class ExecResult:
    exit_code: int
    output: str


class DockerService:
    def __init__(self) -> None:
        # Global client timeout prevents Docker API calls from hanging forever.
        self.client = docker.from_env(timeout=settings.docker_api_timeout_seconds)

    def list_containers(self) -> List[Dict[str, Any]]:
        containers = self.client.containers.list(all=True)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "<none>",
            }
            for c in containers
        ]

    def get_container(self, name: str):
        return self.client.containers.get(name)

    def create_container(self, name: str, image: str) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = dict(
            name=name,
            command="sleep infinity",
            detach=True,
            tty=True,
            stdin_open=True,
            network_mode="bridge",
            mem_limit=settings.container_mem_limit,
            nano_cpus=settings.container_nano_cpus,
            pids_limit=settings.container_pids_limit,
            shm_size=settings.container_shm_size,
        )
        if settings.container_platform:
            kwargs["platform"] = settings.container_platform
        container = self.client.containers.run(image, **kwargs)
        return {"id": container.short_id, "name": container.name, "status": container.status}

    def delete_container(self, name: str) -> None:
        container = self.client.containers.get(name)
        container.remove(force=True)

    def exec(self, name: str, cmd: str, timeout: int) -> ExecResult:
        container = self.client.containers.get(name)
        safe_cmd = f"timeout {int(timeout)}s /bin/bash -lc {shlex.quote(cmd)}"
        result = container.exec_run(["/bin/bash", "-lc", safe_cmd], stdout=True, stderr=True, demux=False)
        output = result.output.decode("utf-8", errors="replace") if isinstance(result.output, bytes) else str(result.output)
        return ExecResult(exit_code=result.exit_code, output=output)

    def write_file(self, name: str, path: str, content: bytes) -> None:
        container = self.client.containers.get(name)

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            info = tarfile.TarInfo(name=path.split("/")[-1])
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        tar_buffer.seek(0)

        parent_dir = "/".join(path.split("/")[:-1]) or "/"
        if not container.put_archive(parent_dir, tar_buffer.read()):
            raise APIError("failed to upload archive")

    def read_file_bytes(self, name: str, path: str) -> bytes:
        container = self.client.containers.get(name)
        stream, _ = container.get_archive(path)
        data = b"".join(stream)

        tar_buffer = io.BytesIO(data)
        with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
            members = tar.getmembers()
            if not members:
                return b""
            extracted = tar.extractfile(members[0])
            if extracted is None:
                return b""
            return extracted.read()

    def read_file(self, name: str, path: str) -> str:
        return self.read_file_bytes(name, path).decode("utf-8", errors="replace")


_docker_service: Optional[DockerService] = None


def get_docker_service() -> DockerService:
    global _docker_service
    if _docker_service is None:
        _docker_service = DockerService()
    return _docker_service
